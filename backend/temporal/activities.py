"""
Temporal Activities for Ghost Teammate
--------------------------------------
Each activity is a single unit of work that can be retried independently.
Activities handle: database ops, browser control, email sending, memory.

Key pattern: Activities are synchronous Python functions that Temporal manages.
If one fails, Temporal retries it without restarting the whole workflow.
"""
from temporalio import activity
from backend.services.supabase_client import get_supabase
from backend.services.agent_service import GhostTeammateAgent
from backend.services import steel_service
from backend.services.supermemory_service import get_user_context, add_memory
from backend.services.resend_service import send_approval_request, send_error_email


@activity.defn
async def create_job_record(user_id: str, goal: str) -> str:
    """
    Creates the initial job record in Supabase.
    This is the first activity - tracks the task from start to finish.
    
    Returns: The job ID (UUID string)
    """
    supabase = get_supabase()
    
    job = supabase.table("jobs").insert({
        "user_id": user_id,
        "goal": goal,
        "status": "pending",  # Must be one of: pending, running, waiting_approval, waiting_info, completed, failed, rejected
        "temporal_workflow_id": activity.info().workflow_id
    }).execute()
    
    job_id = job.data[0]['id']
    print(f"📋 Created job record: {job_id}")
    
    return job_id


@activity.defn
async def agent_strategic_planning(user_id: str, goal: str) -> dict:
    """
    Step 1: The agent consults Supermemory and decides strategy.
    
    This is the "think before you act" phase:
    - BROWSER: Need to interact with a web app
    - MEMORY: Can resolve from context alone  
    - CLARIFY: Need more information from user
    
    Returns: dict with 'strategy', 'reasoning', and 'profile'
    """
    # Fetch user context from Supermemory
    profile = get_user_context(user_id, query=goal)
    
    # Initialize the agent brain
    agent = GhostTeammateAgent(user_id=user_id, user_profile=profile)
    
    # Let the agent decide the best approach
    decision = await agent.decide_strategy(goal)
    
    print(f"🧠 Strategy decided: {decision['strategy']}")
    
    return {
        "strategy": decision["strategy"],
        "reasoning": decision["reasoning"],
        "profile": profile
    }


@activity.defn
async def provision_browser_environment(user_id: str, job_id: str) -> str:
    """
    Step 2: Provisions a Steel browser session for the agent.
    
    Creates a cloud-based Chrome instance the agent can control.
    The session_viewer_url allows users to watch in real-time.
    
    Returns: The Steel session ID
    """
    # Create the Steel session
    session = await steel_service.start_teammate_browser(user_id)
    
    # Update the job record with session info
    supabase = get_supabase()
    supabase.table("jobs").update({
        "steel_session_id": session["id"],
        "steel_viewer_url": session["session_viewer_url"],
        "status": "running"
    }).eq("id", job_id).execute()
    
    print(f"🖥️ Browser provisioned. Session: {session['id']}")
    
    return session["id"]


@activity.defn
async def execute_agent_turn(
    session_id: str, 
    goal: str, 
    user_id: str,
    user_profile: dict, 
    job_id: str,
    user_email: str = None
) -> dict:
    """
    Step 3: Executes a single reasoning-action turn in the browser.
    
    One turn = screenshot → think → act → observe result
    
    The workflow calls this in a loop until the agent says it's finished.
    
    Returns: dict with 'reasoning', 'finished', 'action_taken', 'error_type' (if any)
    """
    from backend.services.agent_service import create_agent_with_credentials
    
    try:
        # Initialize agent with credentials loaded
        agent = await create_agent_with_credentials(
            user_id=user_id,
            user_profile=user_profile,
            session_id=session_id
        )
        
        # Execute one reasoning-action cycle
        result = await agent.execute_turn(goal)
        
        # Log the turn to Supabase for the dashboard feed
        supabase = get_supabase()
        supabase.table("task_logs").insert({
            "job_id": job_id,
            "action": result.get("action_taken", "REASONING"),
            "reasoning": result["reasoning"][:1000] if result["reasoning"] else "",  # Truncate long reasoning
            "finished": result["finished"]
        }).execute()
        
        print(f"🔄 Turn complete. Action: {result.get('action_taken', 'None')}. Finished: {result['finished']}")
        
        return result
        
    except Exception as e:
        error_str = str(e).lower()
        error_message = str(e)
        
        # Detect rate limit / quota errors
        if "429" in error_str or "resource_exhausted" in error_str or "rate" in error_str or "quota" in error_str:
            print(f"⚠️ Rate limit detected: {e}")
            
            # Determine error type
            if "quota" in error_str:
                error_type = "quota_exceeded"
            else:
                error_type = "rate_limit"
            
            # Send notification email
            if user_email:
                try:
                    send_error_email(
                        user_email=user_email,
                        user_id=user_id,
                        goal=goal,
                        error_type=error_type,
                        error_message=error_message[:500],
                        is_retryable=True,
                        retry_after_seconds=60
                    )
                    print(f"📧 Error notification sent to {user_email}")
                except Exception as email_err:
                    print(f"⚠️ Failed to send error email: {email_err}")
            
            return {
                "reasoning": f"Rate limit encountered: {error_message[:200]}",
                "finished": True,
                "action_taken": None,
                "error_type": error_type,
                "error_message": error_message[:500]
            }
        
        # Re-raise other errors for Temporal retry
        raise


@activity.defn
async def request_approval_activity(
    user_email: str, 
    user_id: str, 
    workflow_id: str, 
    action_description: str
) -> dict:
    """
    HITL Safety Gate: Requests human approval for high-stakes actions.
    
    Called when the agent detects a potentially destructive action.
    The workflow pauses until the user clicks Approve or Reject.
    
    Returns: dict with 'email_sent' status
    """
    try:
        result = send_approval_request(
            user_email=user_email,
            user_id=user_id,
            workflow_id=workflow_id,
            action=action_description
        )
        
        print(f"📧 Approval email sent to {user_email}")
        
        # Log to Supabase for the dashboard
        supabase = get_supabase()
        supabase.table("approvals").insert({
            "workflow_id": workflow_id,
            "user_email": user_email,
            "action_type": "high_stakes",
            "description": action_description[:500],  # Truncate
            "status": "pending"
        }).execute()
        
        return {"email_sent": True, "resend_id": result.get("id")}
    except Exception as e:
        print(f"⚠️ Failed to send approval email: {e}")
        return {"email_sent": False, "error": str(e)}


@activity.defn
async def update_job_status(job_id: str, status: str) -> None:
    """
    Updates the high-level job status in Supabase.
    
    Status values: 'initializing', 'running', 'waiting_approval', 
                   'waiting_info', 'completed', 'failed', 'rejected'
    """
    supabase = get_supabase()
    supabase.table("jobs").update({"status": status}).eq("id", job_id).execute()
    
    print(f"📊 Job {job_id[:8]}... status → {status}")


@activity.defn
async def send_completion_email(
    user_email: str, 
    user_id: str, 
    goal: str,
    summary: str,
    actions_taken: list = None
) -> dict:
    """
    Sends a summary email when the task is complete.
    This is the "pulse update" letting the user know the agent finished.
    """
    from backend.services.resend_service import send_completion_email as _send_completion_email
    
    try:
        result = _send_completion_email(
            user_email=user_email,
            user_id=user_id,
            goal=goal,
            summary=summary,
            actions_taken=actions_taken
        )
        return {"sent": True}
    except Exception as e:
        print(f"⚠️ Failed to send completion email: {e}")
        return {"sent": False, "error": str(e)}


@activity.defn
async def send_task_started_email_activity(
    user_email: str,
    user_id: str,
    goal: str
) -> dict:
    """
    Sends confirmation that the task has started.
    """
    from backend.services.resend_service import send_task_started_email
    
    try:
        result = send_task_started_email(
            user_email=user_email,
            user_id=user_id,
            goal=goal
        )
        return {"sent": True}
    except Exception as e:
        print(f"⚠️ Failed to send task started email: {e}")
        return {"sent": False, "error": str(e)}


@activity.defn
async def send_error_email_activity(
    user_email: str,
    user_id: str,
    goal: str,
    error_type: str,
    error_message: str
) -> dict:
    """
    Sends an error notification email.
    """
    try:
        result = send_error_email(
            user_email=user_email,
            user_id=user_id,
            goal=goal,
            error_type=error_type,
            error_message=error_message,
            is_retryable=True
        )
        return {"sent": True}
    except Exception as e:
        print(f"⚠️ Failed to send error email: {e}")
        return {"sent": False, "error": str(e)}


@activity.defn
async def save_task_memory(user_id: str, goal: str, outcome: str) -> bool:
    """
    Saves the completed task to Supermemory for future context.
    This helps the agent learn user patterns over time.
    """
    memory_content = f"Task: {goal}\nOutcome: {outcome}"
    
    success = add_memory(
        user_id=user_id,
        content=memory_content,
        metadata={"type": "completed_task"}
    )
    
    if success:
        print(f"📝 Task saved to memory for user {user_id[:8]}...")
    
    return success


@activity.defn
async def release_browser_session(session_id: str) -> None:
    """
    Releases the Steel browser session to free resources.
    Called after task completion or failure.
    """
    await steel_service.release_session(session_id)
