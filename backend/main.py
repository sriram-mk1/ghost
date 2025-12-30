"""
Ghost Teammate API
------------------
FastAPI server that handles:
1. Inbound email webhooks from Resend (agent wakeup)
2. HITL approval/rejection webhooks
3. Task launch endpoint for the dashboard
4. Health checks

Run with:
    cd /path/to/ghost
    export PYTHONPATH=$PYTHONPATH:$(pwd)
    source venv/bin/activate
    uvicorn backend.main:app --reload --port 8000
"""
from fastapi import FastAPI, Request, HTTPException, Header, Query, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from temporalio.client import Client
import uuid
from backend.core.config import get_settings
from backend.temporal.workflows import GhostTeammateWorkflow

app = FastAPI(
    title="The Ghost Teammate API",
    description="Headless AI agent that acts as your remote teammate",
    version="1.0.0"
)

settings = get_settings()

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================
# Health Check
# =============================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "The Ghost Teammate is active.",
        "version": "1.0.0"
    }


# =============================================
# Favicon & Static Assets (Silence 404s)
# =============================================

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/apple-touch-icon.png", include_in_schema=False)
async def apple_touch_icon():
    return Response(status_code=204)

@app.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
async def apple_touch_icon_precomposed():
    return Response(status_code=204)


# =============================================
# Task Launch (Dashboard)
# =============================================

@app.post("/tasks/launch")
async def launch_task(
    goal: str = Query(..., description="The task description"),
    user_id: str = Query(..., description="User identifier"),
    user_email: str = Query(..., description="User email for notifications")
):
    """
    Launch a new task from the dashboard.
    
    This creates a Temporal workflow that will:
    1. Consult Supermemory for context
    2. Provision a browser if needed
    3. Execute the task with HITL safety checks
    """
    try:
        client = await Client.connect(settings.TEMPORAL_ADDRESS)
        workflow_id = f"dashboard-{uuid.uuid4()}"
        
        await client.start_workflow(
            GhostTeammateWorkflow.run,
            args=[goal, user_id, user_email],
            id=workflow_id,
            task_queue="ghost-teammate-queue",
        )
        
        return {
            "status": "success",
            "workflow_id": workflow_id,
            "message": "Task launched successfully"
        }
    except Exception as e:
        print(f"❌ Failed to launch task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# Resend Inbound Email Webhook
# =============================================

@app.post("/webhooks/resend/inbound")
async def resend_inbound_webhook(request: Request):
    """
    Handles inbound emails from Resend.
    
    IMPORTANT: The webhook payload does NOT contain the email body!
    We must fetch the full content using Resend's receiving API with the email_id.
    
    User identification:
    1. Look up sender's email in the profiles table
    2. That's it! No complex sub-addressing needed.
    
    Users just email ghost@yourdomain.com and we identify them by their email.
    """
    from backend.services.supabase_client import get_supabase
    from backend.services.resend_service import get_email_content_by_id
    import re
    
    raw_payload = await request.json()
    
    # Debug: Log the full payload structure
    print(f"📨 Inbound email webhook received:")
    print(f"   Raw payload keys: {list(raw_payload.keys())}")
    
    # Resend wraps inbound emails in a 'data' object with 'type' and 'created_at'
    # The actual email metadata is inside 'data'
    if "data" in raw_payload and "type" in raw_payload:
        print(f"   Event type: {raw_payload.get('type')}")
        payload = raw_payload.get("data", {})
        print(f"   Data keys: {list(payload.keys())}")
    else:
        # Direct format (older or different webhook config)
        payload = raw_payload
    
    # Get the email_id - THIS IS CRITICAL for fetching the actual body
    email_id = payload.get("email_id") or payload.get("id") or payload.get("emailId")
    
    # Extract email metadata from webhook (for sender identification)
    from_email_raw = payload.get("from", "") or payload.get("sender", "") or ""
    subject = payload.get("subject", "No Subject")
    to_emails = payload.get("to", [])
    in_reply_to = payload.get("in_reply_to") or payload.get("inReplyTo")
    thread_id = payload.get("thread_id") or payload.get("threadId")
    
    # Fallback text content from webhook (usually empty or minimal)
    webhook_text = payload.get("text", "") or payload.get("plain", "") or payload.get("body", "") or ""
    
    print(f"   Email ID: {email_id}")
    print(f"   From (raw): {from_email_raw}")
    print(f"   Subject: {subject}")
    print(f"   To: {to_emails}")
    print(f"   Webhook text preview: {webhook_text[:100] if webhook_text else '(empty)'}...")
    
    # =========================================================================
    # FETCH ACTUAL EMAIL CONTENT FROM RESEND API
    # =========================================================================
    text_content = webhook_text  # Start with webhook content as fallback
    
    if email_id:
        print(f"📧 Fetching full email content from Resend API...")
        email_data = await get_email_content_by_id(email_id)
        
        if email_data.get("success"):
            # Use the fetched content
            fetched_text = email_data.get("text", "")
            fetched_subject = email_data.get("subject", "")
            
            if fetched_text:
                text_content = fetched_text
                print(f"   ✅ Got email body: {len(text_content)} chars")
            else:
                print(f"   ⚠️ API returned empty text, using webhook fallback")
            
            # Use API subject if webhook didn't have it
            if fetched_subject and (not subject or subject == "No Subject"):
                subject = fetched_subject
        else:
            print(f"   ⚠️ Could not fetch from API: {email_data.get('error')}")
            print(f"   Using webhook payload as fallback")
    else:
        print(f"   ⚠️ No email_id in payload, using webhook content directly")
    
    # Validate we have content
    if not text_content or len(text_content.strip()) < 3:
        print(f"   ❌ No email body content found!")
        # Try HTML as last resort
        html_content = payload.get("html", "")
        if html_content:
            # Strip HTML tags for basic text extraction
            import re as regex
            text_content = regex.sub(r'<[^>]+>', '', html_content)[:2000]
            print(f"   📄 Extracted {len(text_content)} chars from HTML")
    
    print(f"   📝 Final text content: {text_content[:200] if text_content else '(still empty)'}...")
    
    # Extract clean email address from various formats:
    # - "user@example.com"
    # - "Name <user@example.com>"
    # - "<user@example.com>"
    def extract_email(raw: str) -> str:
        if not raw:
            return ""
        raw = raw.strip()
        # Try to extract from angle brackets
        match = re.search(r'<([^>]+)>', raw)
        if match:
            return match.group(1).lower().strip()
        # Check if it's already a plain email
        if '@' in raw and ' ' not in raw:
            return raw.lower().strip()
        # Last resort: find email pattern
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw)
        if match:
            return match.group(0).lower().strip()
        return raw.lower().strip()
    
    clean_email = extract_email(from_email_raw)
    print(f"   Clean email: {clean_email}")
    
    # Look up user - multiple strategies
    user_id = None
    supabase = get_supabase()
    
    # Strategy 1: Extract UUID from the 'to' address sub-addressing
    # e.g., assistant+3614a810-dd08-47e4-a283-62740096f548@reluit.com
    for to_addr in to_emails:
        if "+" in to_addr and "@" in to_addr:
            try:
                # Extract the part between + and @
                sub_part = to_addr.split("+")[1].split("@")[0]
                # Check if it looks like a UUID (36 chars with dashes)
                if len(sub_part) == 36 and sub_part.count("-") == 4:
                    # Verify this user exists
                    check = supabase.table("profiles").select("id, full_name").eq("id", sub_part).execute()
                    if check.data and len(check.data) > 0:
                        user_id = sub_part
                        print(f"✅ Identified user from sub-address: {check.data[0].get('full_name')} ({user_id[:8]}...)")
                        break
                    else:
                        print(f"⚠️ UUID in sub-address not found in profiles: {sub_part[:8]}...")
            except (IndexError, ValueError):
                pass
    
    # Strategy 2: Look up by sender's email address
    if not user_id:
        try:
            response = supabase.table("profiles").select("id, full_name").eq("email_address", clean_email).execute()
            
            if response.data and len(response.data) > 0:
                user_id = response.data[0]['id']
                user_name = response.data[0].get('full_name', 'Unknown')
                print(f"✅ Identified user by sender email: {user_name} ({user_id[:8]}...)")
            else:
                print(f"⚠️ No profile found for sender email: {clean_email}")
                
                # Try case-insensitive search as fallback
                response = supabase.table("profiles").select("id, full_name, email_address").execute()
                for profile in (response.data or []):
                    if profile.get('email_address', '').lower() == clean_email:
                        user_id = profile['id']
                        print(f"✅ Found user via case-insensitive match: {profile.get('full_name')}")
                        break
                        
        except Exception as e:
            print(f"❌ Error looking up user: {e}")

    # If still no user_id, we can't process - user must sign up first
    # (profiles table has a foreign key to auth.users, so we can't auto-create)
    if not user_id:
        print(f"❌ Unknown sender: {clean_email}")
        print(f"   User must sign up at the dashboard first before emailing the agent.")
        
        # TODO: Optionally send a welcome/signup email back to the sender
        # from backend.services.resend_service import send_teammate_email
        # send_welcome_email(clean_email)
        
        return {
            "status": "ignored", 
            "reason": "unknown_user",
            "email": clean_email,
            "hint": "Please sign up at the dashboard first, then email the agent."
        }

    # Check if this is a reply to an existing conversation
    # Try to find a running workflow for this user
    if in_reply_to or thread_id or subject.lower().startswith("re:"):
        try:
            supabase = get_supabase()
            
            # Find the most recent running job for this user
            result = supabase.table("jobs").select(
                "temporal_workflow_id"
            ).eq("user_id", user_id).in_(
                "status", ["running", "waiting_approval", "waiting_info"]
            ).order("created_at", desc=True).limit(1).execute()
            
            if result.data and result.data[0].get("temporal_workflow_id"):
                # This is a mid-task reply - route to existing workflow
                workflow_id = result.data[0]["temporal_workflow_id"]
                
                client = await Client.connect(settings.TEMPORAL_ADDRESS)
                handle = client.get_workflow_handle(workflow_id)
                await handle.signal("user_message", text_content)
                
                print(f"📧 Email routed to existing workflow: {workflow_id}")
                return {"status": "success", "workflow_id": workflow_id, "type": "reply"}
                
        except Exception as e:
            print(f"⚠️ Failed to route reply, creating new workflow: {e}")
    
    # Start a new Temporal workflow
    try:
        client = await Client.connect(settings.TEMPORAL_ADDRESS)
        workflow_id = f"email-{uuid.uuid4()}"
        
        goal = f"Subject: {subject}\n\n{text_content}"
        
        await client.start_workflow(
            GhostTeammateWorkflow.run,
            args=[goal, user_id, clean_email],  # Use clean_email (the sender's email)
            id=workflow_id,
            task_queue="ghost-teammate-queue",
        )
        
        print(f"📧 Email triggered new workflow: {workflow_id}")
        return {"status": "success", "workflow_id": workflow_id, "type": "new"}
        
    except Exception as e:
        print(f"❌ Failed to start workflow from email: {e}")
        return {"status": "error", "message": str(e)}


# =============================================
# HITL Approval/Rejection Webhooks
# =============================================

@app.get("/webhooks/resend/approve")
async def approve_task(workflow_id: str = Query(...)):
    """
    Called when user clicks 'Approve' in the HITL email.
    Sends a signal to the waiting Temporal workflow.
    """
    try:
        client = await Client.connect(settings.TEMPORAL_ADDRESS)
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal("approve")
        
        print(f"✅ Workflow {workflow_id} approved")
        
        # Return a nice HTML page
        return HTMLResponse("""
            <html>
            <head><title>Approved</title></head>
            <body style="font-family: system-ui; display: flex; justify-content: center; align-items: center; height: 100vh; background: #0a0a0b; color: white;">
                <div style="text-align: center;">
                    <h1 style="color: #22c55e;">✓ Approved</h1>
                    <p>Your Ghost Teammate will continue with the action.</p>
                </div>
            </body>
            </html>
        """)
    except Exception as e:
        print(f"❌ Failed to approve workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/webhooks/resend/reject")
async def reject_task(workflow_id: str = Query(...)):
    """
    Called when user clicks 'Reject' in the HITL email.
    Sends a signal to abort the workflow.
    """
    try:
        client = await Client.connect(settings.TEMPORAL_ADDRESS)
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal("reject")
        
        print(f"🚫 Workflow {workflow_id} rejected")
        
        return HTMLResponse("""
            <html>
            <head><title>Rejected</title></head>
            <body style="font-family: system-ui; display: flex; justify-content: center; align-items: center; height: 100vh; background: #0a0a0b; color: white;">
                <div style="text-align: center;">
                    <h1 style="color: #ef4444;">✗ Rejected</h1>
                    <p>The action has been cancelled.</p>
                </div>
            </body>
            </html>
        """)
    except Exception as e:
        print(f"❌ Failed to reject workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# Webhook Status (for Resend event types)
# =============================================

@app.post("/webhooks/resend/status")
async def resend_status_webhook(request: Request):
    """
    Handles email delivery status events from Resend.
    
    Event types: email.sent, email.delivered, email.bounced, 
                 email.complained, email.opened, email.clicked
    """
    payload = await request.json()
    event_type = payload.get("type", "unknown")
    email_id = payload.get("data", {}).get("email_id", "unknown")
    
    print(f"📬 Email event: {event_type} for {email_id}")
    
    # You could update Supabase here to track email delivery
    return {"status": "received"}


# =============================================
# Kill Switch & Task Control
# =============================================

@app.post("/tasks/{workflow_id}/kill")
async def kill_task(workflow_id: str):
    """
    KILL SWITCH - immediately stops a running task.
    
    Use this from the dashboard when you need to abort a task.
    The workflow will clean up resources (browser session, etc.).
    """
    try:
        client = await Client.connect(settings.TEMPORAL_ADDRESS)
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal("kill")
        
        print(f"💀 Workflow {workflow_id} killed")
        return {"status": "success", "message": "Task killed successfully"}
        
    except Exception as e:
        print(f"❌ Failed to kill workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/{workflow_id}/message")
async def send_user_message(
    workflow_id: str,
    message: str = Query(..., description="Additional instructions for the agent")
):
    """
    Send a mid-task message to the agent.
    
    Use this when you want to give the agent additional context
    or change direction while a task is running.
    """
    try:
        client = await Client.connect(settings.TEMPORAL_ADDRESS)
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal("user_message", message)
        
        print(f"💬 Message sent to workflow {workflow_id}")
        return {"status": "success", "message": "Message sent to agent"}
        
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{workflow_id}/status")
async def get_task_status(workflow_id: str):
    """
    Query the status of a running workflow.
    
    Returns approval state, pending messages, etc.
    """
    try:
        client = await Client.connect(settings.TEMPORAL_ADDRESS)
        handle = client.get_workflow_handle(workflow_id)
        status = await handle.query("get_status")
        
        return {"status": "success", "data": status}
        
    except Exception as e:
        print(f"❌ Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# Agent Account Management
# =============================================

@app.post("/agent/accounts/create")
async def create_agent_account(
    user_id: str = Query(..., description="User identifier"),
    platform: str = Query(..., description="Platform name (e.g., Notion, Linear)"),
    platform_url: str = Query(..., description="Platform base URL (e.g., https://notion.so)")
):
    """
    Creates a new agent account for a platform.
    
    This generates:
    - A unique agent email for this user+platform
    - A secure password (stored in Steel, not returned)
    - Credentials are auto-injected when the agent logs in
    
    The agent can then sign up / log in to the platform using these credentials.
    """
    from backend.services.credentials_service import create_agent_account as create_creds
    
    try:
        result = await create_creds(
            user_id=user_id,
            platform=platform,
            platform_url=platform_url
        )
        return result
    except Exception as e:
        print(f"❌ Failed to create agent account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/accounts")
async def list_agent_accounts(user_id: str = Query(...)):
    """
    Lists all agent accounts for a user.
    """
    from backend.services.supabase_client import get_supabase
    
    supabase = get_supabase()
    result = supabase.table("workspaces").select(
        "platform_name, agent_email, is_active, created_at"
    ).eq("user_id", user_id).execute()
    
    return {"accounts": result.data or []}


# =============================================
# Debug Endpoints (Development Only)
# =============================================

@app.get("/debug/profiles")
async def debug_list_profiles():
    """
    DEBUG: List all profiles in the database.
    Remove this endpoint in production!
    """
    from backend.services.supabase_client import get_supabase
    
    supabase = get_supabase()
    result = supabase.table("profiles").select("id, email_address, full_name, created_at").execute()
    
    return {
        "count": len(result.data or []),
        "profiles": [
            {
                "id": p["id"][:8] + "...",
                "email": p.get("email_address"),
                "name": p.get("full_name"),
                "created": p.get("created_at")
            }
            for p in (result.data or [])
        ]
    }


@app.get("/debug/lookup/{email}")
async def debug_lookup_email(email: str):
    """
    DEBUG: Test email lookup.
    """
    from backend.services.supabase_client import get_supabase
    
    supabase = get_supabase()
    
    # Direct lookup
    result = supabase.table("profiles").select("id, email_address, full_name").eq("email_address", email.lower()).execute()
    
    if result.data:
        return {"found": True, "profile": result.data[0]}
    
    # Case-insensitive fallback
    all_profiles = supabase.table("profiles").select("id, email_address, full_name").execute()
    for p in (all_profiles.data or []):
        if p.get("email_address", "").lower() == email.lower():
            return {"found": True, "profile": p, "method": "case_insensitive"}
    
    return {"found": False, "searched_for": email.lower()}


# =============================================
# Entry Point
# =============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
