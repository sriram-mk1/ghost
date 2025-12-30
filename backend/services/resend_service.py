"""
Resend Email Service
--------------------
Handles all email communication for the Ghost Teammate:
1. Sending emails FROM the agent's identity
2. Human-in-the-Loop approval requests
3. Task completion summaries
4. Error notifications (rate limits, etc.)

Email Strategy:
- Outbound: ghost@yourdomain.com (friendly, consistent)
- User identification: via email lookup in profiles table
- No complex sub-addressing required!
"""
import resend
from backend.core.config import get_settings
from typing import Optional

settings = get_settings()
resend.api_key = settings.RESEND_API_KEY

# Your verified domain in Resend
# Configure via AGENT_EMAIL_DOMAIN in .env
AGENT_DOMAIN = settings.AGENT_EMAIL_DOMAIN
AGENT_EMAIL = f"ghost@{AGENT_DOMAIN}"

# Brand colors
BRAND_BG = "#0A0A0B"
BRAND_CARD = "#111113"
BRAND_BORDER = "#1e1e22"
BRAND_PRIMARY = "#3b82f6"  # Blue
BRAND_SUCCESS = "#22c55e"  # Green
BRAND_WARNING = "#f59e0b"  # Amber
BRAND_ERROR = "#ef4444"    # Red
BRAND_TEXT = "#e2e8f0"
BRAND_MUTED = "#94a3b8"
BRAND_DIM = "#64748b"


async def get_email_content_by_id(email_id: str) -> dict:
    """
    Fetches the full email content from Resend's receiving API.
    
    The webhook payload only contains metadata, NOT the email body.
    This function retrieves the actual text/html content using the email_id.
    
    Uses the Resend SDK's receiving.get() method which calls:
    GET /emails/receiving/{email_id}
    
    Args:
        email_id: The email ID from the webhook payload
        
    Returns:
        dict with 'text', 'html', 'subject', 'from', 'to', etc.
    """
    from resend.emails._receiving import Receiving
    
    try:
        # Use the Resend SDK's receiving API
        # This calls: GET /emails/receiving/{email_id}
        email = Receiving.get(email_id)
        
        print(f"📧 Retrieved received email content for {email_id}")
        print(f"   Subject: {email.get('subject', 'N/A')}")
        print(f"   Has text: {bool(email.get('text'))}")
        print(f"   Has html: {bool(email.get('html'))}")
        
        return {
            "text": email.get("text", "") or "",
            "html": email.get("html", "") or "",
            "subject": email.get("subject", ""),
            "from": email.get("from", ""),
            "to": email.get("to", []),
            "headers": email.get("headers", {}),
            "success": True
        }
                
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error fetching received email content: {error_msg}")
        return {"success": False, "error": error_msg}


def _get_email_wrapper(content: str, footer_text: str = "") -> str:
    """
    Wraps email content in a beautiful branded container.
    """
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Ghost Teammate</title>
    </head>
    <body style="margin: 0; padding: 0; background: {BRAND_BG}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: {BRAND_BG};">
            <tr>
                <td style="padding: 40px 20px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 560px; margin: 0 auto;">
                        <!-- Header with Logo -->
                        <tr>
                            <td style="padding: 0 0 32px 0;">
                                <table role="presentation" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td style="width: 40px; height: 40px; background: linear-gradient(135deg, {BRAND_PRIMARY}, #8b5cf6); border-radius: 10px; text-align: center; vertical-align: middle;">
                                            <span style="font-size: 20px;">👻</span>
                                        </td>
                                        <td style="padding-left: 12px;">
                                            <span style="font-size: 18px; font-weight: 600; color: white; letter-spacing: -0.02em;">Ghost Teammate</span>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Main Content Card -->
                        <tr>
                            <td style="background: {BRAND_CARD}; border: 1px solid {BRAND_BORDER}; border-radius: 12px; padding: 32px;">
                                {content}
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 24px 0 0 0; text-align: center;">
                                <p style="margin: 0 0 8px 0; color: {BRAND_DIM}; font-size: 12px;">
                                    {footer_text or "Reply to this email to continue the conversation."}
                                </p>
                                <p style="margin: 0; color: {BRAND_DIM}; font-size: 11px; opacity: 0.7;">
                                    Powered by Ghost Teammate · Your AI coworker
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    '''


def get_agent_email(user_id: str = None) -> str:
    """
    Returns the agent's friendly email address.
    
    We use a single email (ghost@domain.com) for all users.
    User identification happens via sender email lookup, not sub-addressing.
    
    This is much friendlier than "assistant+a3f8b2c1@domain.com"!
    
    Args:
        user_id: Kept for backwards compatibility, not used.
        
    Returns:
        The agent's email, e.g., "ghost@reluit.com"
    """
    return AGENT_EMAIL


def get_agent_display_name() -> str:
    """Returns the friendly display name for the agent."""
    return "Ghost Teammate"


async def send_agent_email(user_id: str, subject: str, body_text: str) -> dict:
    """
    Send an email from the agent to a user identified by user_id.
    
    This looks up the user's email from Supabase and sends a beautifully
    formatted email. Used by the agent for clarification requests, 
    progress updates, and completion reports.
    
    Args:
        user_id: The user's UUID
        subject: Email subject line
        body_text: Plain text body (will be converted to HTML)
        
    Returns:
        Resend API response
    """
    from backend.services.supabase_client import get_supabase
    
    supabase = get_supabase()
    
    # Look up user email from profiles
    result = supabase.table("profiles").select("email").eq("id", user_id).single().execute()
    
    if not result.data or not result.data.get("email"):
        raise ValueError(f"Could not find email for user {user_id}")
    
    user_email = result.data["email"]
    
    # Convert plain text to HTML with proper formatting
    body_html_content = body_text.replace('\n', '<br>')
    
    content = f'''
        <div style="font-size: 14px; color: {BRAND_TEXT}; line-height: 1.7;">
            {body_html_content}
        </div>
    '''
    
    html = _get_email_wrapper(content)
    
    return send_teammate_email(
        user_email=user_email,
        user_id=user_id,
        subject=subject,
        body_html=html
    )


def send_teammate_email(
    user_email: str, 
    user_id: str, 
    subject: str, 
    body_html: str,
    thread_id: str = None
) -> dict:
    """
    Sends an email FROM the agent TO the user.
    
    The 'from' address is the agent's unique identity, making replies
    route back through the inbound webhook with the user_id embedded.
    
    Args:
        user_email: Recipient email
        user_id: Used to generate agent's reply-to address
        subject: Email subject
        body_html: HTML email body
        thread_id: Optional Resend thread ID for conversation threading
        
    Returns:
        Resend API response with email ID
    """
    agent_identity = get_agent_email(user_id)
    
    params = {
        "from": f"Ghost Teammate <{agent_identity}>",
        "to": [user_email],
        "subject": subject,
        "html": body_html,
        "reply_to": agent_identity
    }
    
    # Add thread headers for conversation threading
    if thread_id:
        params["headers"] = {
            "In-Reply-To": thread_id,
            "References": thread_id
        }
    
    return resend.Emails.send(params)


def send_approval_request(
    user_email: str, 
    user_id: str, 
    workflow_id: str, 
    action: str
) -> dict:
    """
    Sends a Human-in-the-Loop approval email.
    
    This is called when the agent detects a high-stakes action
    (delete, pay, etc.) and needs explicit user permission.
    
    The email contains Approve/Reject buttons that link to
    webhook endpoints which signal the Temporal workflow.
    """
    approve_url = f"{settings.BACKEND_URL}/webhooks/resend/approve?workflow_id={workflow_id}"
    reject_url = f"{settings.BACKEND_URL}/webhooks/resend/reject?workflow_id={workflow_id}"
    
    content = f'''
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="display: inline-block; width: 56px; height: 56px; background: rgba(245, 158, 11, 0.1); border-radius: 16px; line-height: 56px; font-size: 28px;">
                ⚠️
            </div>
        </div>
        
        <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 600; color: white; text-align: center;">
            Approval Required
        </h1>
        <p style="margin: 0 0 24px 0; color: {BRAND_MUTED}; font-size: 14px; text-align: center; line-height: 1.5;">
            Your Ghost Teammate wants to perform an action that requires your explicit approval.
        </p>
        
        <div style="background: {BRAND_BG}; border-left: 3px solid {BRAND_WARNING}; padding: 16px 20px; margin: 0 0 24px 0; border-radius: 0 8px 8px 0;">
            <p style="margin: 0 0 6px 0; font-size: 11px; color: {BRAND_DIM}; text-transform: uppercase; letter-spacing: 0.1em;">
                Proposed Action
            </p>
            <p style="margin: 0; font-size: 14px; color: white; line-height: 1.5;">
                {action}
            </p>
        </div>
        
        <p style="margin: 0 0 24px 0; color: {BRAND_MUTED}; font-size: 13px; line-height: 1.5;">
            This action may modify or delete data. Please review carefully before proceeding.
        </p>
        
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
            <tr>
                <td style="padding-right: 8px; width: 50%;">
                    <a href="{approve_url}" style="display: block; background: {BRAND_SUCCESS}; color: white; padding: 14px 24px; text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: 600; text-align: center;">
                        ✓ Approve
                    </a>
                </td>
                <td style="padding-left: 8px; width: 50%;">
                    <a href="{reject_url}" style="display: block; background: {BRAND_ERROR}; color: white; padding: 14px 24px; text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: 600; text-align: center;">
                        ✗ Reject
                    </a>
                </td>
            </tr>
        </table>
        
        <p style="margin: 24px 0 0 0; color: {BRAND_DIM}; font-size: 11px; text-align: center;">
            Workflow ID: {workflow_id[:20]}...
        </p>
    '''
    
    html = _get_email_wrapper(content, "This link expires in 24 hours.")
    
    return send_teammate_email(
        user_email=user_email,
        user_id=user_id,
        subject="⚠️ Action Requires Your Approval",
        body_html=html
    )


def send_task_started_email(
    user_email: str,
    user_id: str,
    goal: str,
    dashboard_url: Optional[str] = None
) -> dict:
    """
    Sends an email confirming the task has started.
    """
    dash_link = dashboard_url or f"{settings.FRONTEND_URL}/dashboard"
    
    content = f'''
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="display: inline-block; width: 56px; height: 56px; background: rgba(59, 130, 246, 0.1); border-radius: 16px; line-height: 56px; font-size: 28px;">
                🚀
            </div>
        </div>
        
        <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 600; color: white; text-align: center;">
            Task Started
        </h1>
        <p style="margin: 0 0 24px 0; color: {BRAND_MUTED}; font-size: 14px; text-align: center; line-height: 1.5;">
            I'm on it! Here's what I'm working on:
        </p>
        
        <div style="background: {BRAND_BG}; border: 1px solid {BRAND_BORDER}; padding: 16px 20px; margin: 0 0 24px 0; border-radius: 8px;">
            <p style="margin: 0 0 6px 0; font-size: 11px; color: {BRAND_DIM}; text-transform: uppercase; letter-spacing: 0.1em;">
                Your Request
            </p>
            <p style="margin: 0; font-size: 14px; color: white; line-height: 1.5;">
                {goal[:500]}{"..." if len(goal) > 500 else ""}
            </p>
        </div>
        
        <a href="{dash_link}" style="display: block; background: {BRAND_PRIMARY}; color: white; padding: 14px 24px; text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: 600; text-align: center;">
            Watch Live in Dashboard →
        </a>
        
        <p style="margin: 24px 0 0 0; color: {BRAND_MUTED}; font-size: 13px; text-align: center; line-height: 1.5;">
            I'll email you when I'm done or if I need your input.
        </p>
    '''
    
    html = _get_email_wrapper(content)
    
    return send_teammate_email(
        user_email=user_email,
        user_id=user_id,
        subject="🚀 Working on your task",
        body_html=html
    )


def send_completion_email(
    user_email: str,
    user_id: str,
    goal: str,
    summary: str,
    actions_taken: Optional[list] = None,
    duration_seconds: Optional[int] = None
) -> dict:
    """
    Sends a beautiful summary email when the task is complete.
    """
    # Format duration
    duration_text = ""
    if duration_seconds:
        if duration_seconds < 60:
            duration_text = f"{duration_seconds}s"
        else:
            mins = duration_seconds // 60
            secs = duration_seconds % 60
            duration_text = f"{mins}m {secs}s"
    
    # Format actions
    actions_html = ""
    if actions_taken and len(actions_taken) > 0:
        action_items = "".join([
            f'<li style="margin: 8px 0; color: {BRAND_TEXT}; font-size: 13px;">{action}</li>'
            for action in actions_taken[:5]
        ])
        if len(actions_taken) > 5:
            action_items += f'<li style="margin: 8px 0; color: {BRAND_DIM}; font-size: 13px;">...and {len(actions_taken) - 5} more</li>'
        
        actions_html = f'''
            <div style="background: {BRAND_BG}; border: 1px solid {BRAND_BORDER}; padding: 16px 20px; margin: 0 0 24px 0; border-radius: 8px;">
                <p style="margin: 0 0 12px 0; font-size: 11px; color: {BRAND_DIM}; text-transform: uppercase; letter-spacing: 0.1em;">
                    Actions Taken
                </p>
                <ul style="margin: 0; padding-left: 20px;">
                    {action_items}
                </ul>
            </div>
        '''
    
    content = f'''
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="display: inline-block; width: 56px; height: 56px; background: rgba(34, 197, 94, 0.1); border-radius: 16px; line-height: 56px; font-size: 28px;">
                ✅
            </div>
        </div>
        
        <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 600; color: {BRAND_SUCCESS}; text-align: center;">
            Task Completed
        </h1>
        <p style="margin: 0 0 24px 0; color: {BRAND_MUTED}; font-size: 14px; text-align: center; line-height: 1.5;">
            I've finished working on your request{f" in {duration_text}" if duration_text else ""}.
        </p>
        
        <!-- Original Request -->
        <div style="background: {BRAND_BG}; border: 1px solid {BRAND_BORDER}; padding: 16px 20px; margin: 0 0 16px 0; border-radius: 8px;">
            <p style="margin: 0 0 6px 0; font-size: 11px; color: {BRAND_DIM}; text-transform: uppercase; letter-spacing: 0.1em;">
                Original Request
            </p>
            <p style="margin: 0; font-size: 14px; color: white; line-height: 1.5;">
                {goal[:300]}{"..." if len(goal) > 300 else ""}
            </p>
        </div>
        
        <!-- Summary -->
        <div style="background: {BRAND_BG}; border-left: 3px solid {BRAND_SUCCESS}; padding: 16px 20px; margin: 0 0 24px 0; border-radius: 0 8px 8px 0;">
            <p style="margin: 0 0 6px 0; font-size: 11px; color: {BRAND_DIM}; text-transform: uppercase; letter-spacing: 0.1em;">
                Summary
            </p>
            <p style="margin: 0; font-size: 14px; color: white; line-height: 1.6;">
                {summary[:600]}{"..." if len(summary) > 600 else ""}
            </p>
        </div>
        
        {actions_html}
        
        <p style="margin: 0; color: {BRAND_MUTED}; font-size: 13px; text-align: center; line-height: 1.5;">
            Reply to this email to give me another task.
        </p>
    '''
    
    html = _get_email_wrapper(content)
    
    return send_teammate_email(
        user_email=user_email,
        user_id=user_id,
        subject="✅ Task Completed",
        body_html=html
    )


def send_error_email(
    user_email: str,
    user_id: str,
    goal: str,
    error_type: str,
    error_message: str,
    is_retryable: bool = True,
    retry_after_seconds: Optional[int] = None
) -> dict:
    """
    Sends an error notification email.
    Used for rate limits, API errors, and other failures.
    """
    # Customize messaging based on error type
    if error_type == "rate_limit":
        icon = "⏳"
        title = "Rate Limit Reached"
        subtitle = "The AI service is temporarily rate-limited."
        if retry_after_seconds:
            retry_text = f"The system will automatically retry in {retry_after_seconds} seconds."
        else:
            retry_text = "Please wait a few minutes and try again."
    elif error_type == "quota_exceeded":
        icon = "📊"
        title = "Quota Exceeded"
        subtitle = "Daily or monthly usage limits have been reached."
        retry_text = "Your quota will reset soon. Consider upgrading for higher limits."
    elif error_type == "api_error":
        icon = "⚡"
        title = "Service Temporarily Unavailable"
        subtitle = "There was an issue connecting to the AI service."
        retry_text = "This is usually temporary. Please try again in a few minutes." if is_retryable else "Please contact support if this persists."
    else:
        icon = "❌"
        title = "Task Failed"
        subtitle = "Something went wrong while processing your request."
        retry_text = "Please try again or contact support." if is_retryable else "Please contact support for assistance."
    
    content = f'''
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="display: inline-block; width: 56px; height: 56px; background: rgba(239, 68, 68, 0.1); border-radius: 16px; line-height: 56px; font-size: 28px;">
                {icon}
            </div>
        </div>
        
        <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 600; color: {BRAND_ERROR}; text-align: center;">
            {title}
        </h1>
        <p style="margin: 0 0 24px 0; color: {BRAND_MUTED}; font-size: 14px; text-align: center; line-height: 1.5;">
            {subtitle}
        </p>
        
        <!-- Original Request -->
        <div style="background: {BRAND_BG}; border: 1px solid {BRAND_BORDER}; padding: 16px 20px; margin: 0 0 16px 0; border-radius: 8px;">
            <p style="margin: 0 0 6px 0; font-size: 11px; color: {BRAND_DIM}; text-transform: uppercase; letter-spacing: 0.1em;">
                Your Request
            </p>
            <p style="margin: 0; font-size: 14px; color: white; line-height: 1.5;">
                {goal[:300]}{"..." if len(goal) > 300 else ""}
            </p>
        </div>
        
        <!-- Error Details -->
        <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); padding: 16px 20px; margin: 0 0 24px 0; border-radius: 8px;">
            <p style="margin: 0 0 6px 0; font-size: 11px; color: {BRAND_ERROR}; text-transform: uppercase; letter-spacing: 0.1em;">
                Error Details
            </p>
            <p style="margin: 0; font-size: 13px; color: {BRAND_MUTED}; line-height: 1.5; font-family: monospace;">
                {error_message[:400]}{"..." if len(error_message) > 400 else ""}
            </p>
        </div>
        
        <p style="margin: 0 0 24px 0; color: {BRAND_MUTED}; font-size: 14px; text-align: center; line-height: 1.5;">
            {retry_text}
        </p>
        
        {"<p style='margin: 0; color: " + BRAND_MUTED + "; font-size: 13px; text-align: center;'>Reply to this email to try again.</p>" if is_retryable else ""}
    '''
    
    html = _get_email_wrapper(content, "We apologize for the inconvenience.")
    
    return send_teammate_email(
        user_email=user_email,
        user_id=user_id,
        subject=f"{icon} {title}",
        body_html=html
    )
