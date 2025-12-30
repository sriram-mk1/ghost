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
# AgentMail Inbound Email Webhook (NEW)
# =============================================

@app.post("/webhooks/agentmail/inbound")
async def agentmail_inbound_webhook(request: Request):
    """
    Handles inbound emails from AgentMail.
    
    Payload:
    - event_types: ["message.received"]
    - payload contains email metadata (or ID to fetch)
    """
    from backend.services.supabase_client import get_supabase
    from backend.services.agentmail_service import get_email_content_by_id
    import re
    
    raw_payload = await request.json()
    
    print(f"📨 Inbound AgentMail webhook received:")
    # print(f"   Payload: {raw_payload}") 
    
    # Adapt to AgentMail payload structure
    # Based on docs, it might be a list of events or a single event
    # We look for "message_id" or "id"
    
    # Safe extraction logic
    payload = raw_payload
    if "webhooks" in raw_payload:
        # It's a list response? unlikely for a webhook event
        pass
    
    # AgentMail webhook structure often has the resource ID in it
    # We will assume a structure like: {"event": "message.created", "data": {...}} or flat
    # If we can't find specific docs, we look for common fields
    
    email_id = payload.get("message_id") or payload.get("id") or payload.get("data", {}).get("id")
    
    # Metadata for immediate use
    subject = payload.get("subject") or payload.get("data", {}).get("subject")
    from_email_raw = payload.get("from_email") or payload.get("from") or payload.get("data", {}).get("from", "")
    to_emails = payload.get("to") or payload.get("data", {}).get("to", [])
    
    # Fetch full content
    text_content = ""
    if email_id:
        print(f"📧 Fetching full email content from AgentMail API for {email_id}...")
        email_data = await get_email_content_by_id(email_id)
        
        if email_data.get("success"):
            text_content = email_data.get("text", "")
            subject = email_data.get("subject", subject) or "No Subject"
            
            # Use API metadata if webhook was sparse
            if not from_email_raw:
                from_email_raw = email_data.get("from", "")
        else:
            print(f"⚠️ Failed to fetch email content: {email_data.get('error')}")
            # Fallback to payload body if available
            text_content = payload.get("text") or payload.get("body") or ""
            
    else:
        print("⚠️ No message_id found in webhook payload. Using raw body if available.")
        text_content = payload.get("text") or payload.get("body") or ""

    if not text_content:
        print("❌ No text content found. Ignoring.")
        return {"status": "ignored", "reason": "no_content"}

    # =========================================================================
    # USER IDENTIFICATION & ROUTING (Same as Resend Logic)
    # =========================================================================
    
    def extract_email(raw: str) -> str:
        if not raw: return ""
        raw = str(raw).strip()
        match = re.search(r'<([^>]+)>', raw)
        if match: return match.group(1).lower().strip()
        if '@' in raw and ' ' not in raw: return raw.lower().strip()
        return raw.lower().strip()
    
    clean_email = extract_email(from_email_raw)
    print(f"   Sender: {clean_email}")
    
    user_id = None
    supabase = get_supabase()
    
    # Lookup User by Email
    try:
        response = supabase.table("profiles").select("id, full_name").eq("email_address", clean_email).execute()
        if response.data:
            user_id = response.data[0]['id']
            print(f"✅ Identified user: {response.data[0].get('full_name')}")
        else:
            # Case-insensitive fallback
            all_profiles = supabase.table("profiles").select("id, email_address").execute()
            for p in (all_profiles.data or []):
                if p.get("email_address", "").lower() == clean_email:
                    user_id = p['id']
                    print(f"✅ Identified user (case-insensitive)")
                    break
    except Exception as e:
        print(f"❌ Error looking up user: {e}")

    if not user_id:
        print(f"❌ Unknown sender: {clean_email}")
        return {"status": "ignored", "reason": "unknown_user", "email": clean_email}

    # Start Workflow
    try:
        client = await Client.connect(settings.TEMPORAL_ADDRESS)
        workflow_id = f"email-{uuid.uuid4()}"
        goal = f"Subject: {subject}\n\n{text_content}"
        
        await client.start_workflow(
            GhostTeammateWorkflow.run,
            args=[goal, user_id, clean_email],
            id=workflow_id,
            task_queue="ghost-teammate-queue",
        )
        print(f"🚀 Started workflow: {workflow_id}")
        return {"status": "success", "workflow_id": workflow_id}
        
    except Exception as e:
        print(f"❌ Failed to start workflow: {e}")
        return {"status": "error", "message": str(e)}


# =============================================
# AgentMail HITL Webhooks
# =============================================

@app.get("/webhooks/agentmail/approve")
async def agentmail_approve(workflow_id: str = Query(...)):
    """Approve task via AgentMail link."""
    return await approve_task_logic(workflow_id)

@app.get("/webhooks/agentmail/reject")
async def agentmail_reject(workflow_id: str = Query(...)):
    """Reject task via AgentMail link."""
    return await reject_task_logic(workflow_id)


# =============================================
# Resend Webhooks (DEPRECATED)
# =============================================

@app.post("/webhooks/resend/inbound")
async def resend_inbound_webhook_deprecated(request: Request):
    """(DEPRECATED) Handles inbound emails from Resend."""
    # ... (Keep existing logic if needed, or redirect/error)
    # For now, we keep it functional but logging warning
    print("⚠️ WARNING: Received deprecated Resend webhook")
    return await resend_inbound_webhook(request)


# Re-using logic helper for approvals to avoid duplication
async def approve_task_logic(workflow_id: str):
    try:
        client = await Client.connect(settings.TEMPORAL_ADDRESS)
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal("approve")
        return HTMLResponse("<html><body style='background:#0a0a0b;color:#22c55e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif;'><h1>✓ Approved</h1></body></html>")
    except Exception as e:
        raise HTTPException(500, str(e))

async def reject_task_logic(workflow_id: str):
    try:
        client = await Client.connect(settings.TEMPORAL_ADDRESS)
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal("reject")
        return HTMLResponse("<html><body style='background:#0a0a0b;color:#ef4444;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif;'><h1>✗ Rejected</h1></body></html>")
    except Exception as e:
        raise HTTPException(500, str(e))

# ... (Original handlers kept below for compatibility if needed, but renamed in routing)
# Note: I am replacing the original route handlers in-place where possible to avoid conflict.

# Keeping the original Approve/Reject routes for backward compatibility with old emails
@app.get("/webhooks/resend/approve")
async def resend_approve_deprecated(workflow_id: str = Query(...)):
    return await approve_task_logic(workflow_id)

@app.get("/webhooks/resend/reject")
async def resend_reject_deprecated(workflow_id: str = Query(...)):
    return await reject_task_logic(workflow_id)




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
