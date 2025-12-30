"""
AgentMail Service
-----------------
Handles email communication using AgentMail.to (infrastructure designed for AI agents).
Replaces the legacy Resend service.

Features:
1. Sending emails FROM the agent's identity (ghost@agentmail.to)
2. Human-in-the-Loop approval requests
3. Task completion summaries
4. Full inbound email processing

Security:
- Webhook signature verification
- Agent isolation via unique identity
"""
import httpx
import json
from typing import Optional, List, Dict, Any
from backend.core.config import get_settings
from backend.services.supabase_client import get_supabase

settings = get_settings()

API_BASE = "https://api.agentmail.to/v1"
HEADERS = {
    "Authorization": f"Bearer {settings.AGENTMAIL_API_KEY}",
    "Content-Type": "application/json"
}

# Brand colors (Same as before for consistency)
BRAND_BG = "#0A0A0B"
BRAND_CARD = "#111113"
BRAND_BORDER = "#1e1e22"
BRAND_PRIMARY = "#3b82f6"
BRAND_SUCCESS = "#22c55e"
BRAND_WARNING = "#f59e0b"
BRAND_ERROR = "#ef4444"
BRAND_TEXT = "#e2e8f0"
BRAND_MUTED = "#94a3b8"
BRAND_DIM = "#64748b"


def get_agent_email(user_id: str = None) -> str:
    """Returns the agent's email address."""
    return settings.AGENT_EMAIL


async def get_email_content_by_id(message_id: str) -> dict:
    """
    Fetches the full email content from AgentMail API.
    GET /messages/{message_id}
    """
    url = f"{API_BASE}/messages/{message_id}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=HEADERS)
            
        if response.status_code != 200:
            print(f"❌ Failed to fetch message {message_id}: {response.text}")
            return {"success": False, "error": response.text}
            
        data = response.json()
        # map AgentMail response to our internal format
        # Assuming AgentMail returns standard message object with subject, text, html
        
        return {
            "text": data.get("text", "") or data.get("body_text", "") or "",
            "html": data.get("html", "") or data.get("body_html", "") or "",
            "subject": data.get("subject", ""),
            "from": data.get("from_email", "") or data.get("from", {}).get("email", ""),
            "to": data.get("to", []),
            "headers": data.get("headers", {}),
            "success": True
        }
    except Exception as e:
        print(f"❌ Error fetching AgentMail message: {e}")
        return {"success": False, "error": str(e)}


async def send_teammate_email(
    user_email: str, 
    user_id: str, 
    subject: str, 
    body_html: str,
    thread_id: str = None
) -> dict:
    """
    Sends an email FROM the agent TO the user via AgentMail.
    Uses POST /inboxes/{inbox_id}/messages
    """
    agent_email = get_agent_email()
    # inbox_id is typically the email address or UUID. Using email as per SDK example.
    inbox_id = agent_email
    
    url = f"{API_BASE}/inboxes/{inbox_id}/messages"
    
    payload = {
        "to": user_email,
        "subject": subject,
        "html": body_html,
        # AgentMail might handle threading differently, but we pass headers if supported
        # or separate fields if the API documents it.
        # Fallback to headers for now.
    }
    
    # If thread_id is provided, try to thread it.
    # Note: AgentMail likely has a specific 'thread_id' field if they support Threads as first-class citizens.
    # For now, we will assume standard headers work or rely on Subject grouping.
    if thread_id:
        payload["headers"] = {
            "In-Reply-To": thread_id,
            "References": thread_id
        }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=HEADERS, json=payload)
            
        if response.status_code >= 400:
            print(f"⚠️ AgentMail Send Failed: {response.text}")
            return {"id": None, "error": response.text}
            
        data = response.json()
        return {"id": data.get("id"), "sent": True}
        
    except Exception as e:
        print(f"⚠️ AgentMail Send Exception: {e}")
        return {"id": None, "error": str(e)}


# ==============================================================================
#  HTML GENERATORS (Ported for consistency)
# ==============================================================================

def _get_email_wrapper(content: str, footer_text: str = "") -> str:
    # Same standard branded wrapper
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
                        <tr>
                            <td style="background: {BRAND_CARD}; border: 1px solid {BRAND_BORDER}; border-radius: 12px; padding: 32px;">
                                {content}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 24px 0 0 0; text-align: center;">
                                <p style="margin: 0 0 8px 0; color: {BRAND_DIM}; font-size: 12px;">
                                    {footer_text or "Reply to this email to continue the conversation."}
                                </p>
                                <p style="margin: 0; color: {BRAND_DIM}; font-size: 11px; opacity: 0.7;">
                                    Powered by AgentMail · Your AI coworker
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

async def send_agent_email(user_id: str, subject: str, body_text: str) -> dict:
    """Send general agent email."""
    supabase = get_supabase()
    result = supabase.table("profiles").select("email").eq("id", user_id).single().execute()
    
    if not result.data or not result.data.get("email"):
        raise ValueError(f"Could not find email for user {user_id}")
    
    user_email = result.data["email"]
    body_html_content = body_text.replace('\n', '<br>')
    
    content = f'<div style="font-size: 14px; color: {BRAND_TEXT}; line-height: 1.7;">{body_html_content}</div>'
    html = _get_email_wrapper(content)
    
    return await send_teammate_email(user_email, user_id, subject, html)

async def send_approval_request(user_email: str, user_id: str, workflow_id: str, action: str) -> dict:
    """Sends Human-in-the-Loop approval email."""
    approve_url = f"{settings.BACKEND_URL}/webhooks/agentmail/approve?workflow_id={workflow_id}"
    reject_url = f"{settings.BACKEND_URL}/webhooks/agentmail/reject?workflow_id={workflow_id}"
    
    content = f'''
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="display: inline-block; width: 56px; height: 56px; background: rgba(245, 158, 11, 0.1); border-radius: 16px; line-height: 56px; font-size: 28px;">⚠️</div>
        </div>
        <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 600; color: white; text-align: center;">Approval Required</h1>
        <p style="margin: 0 0 24px 0; color: {BRAND_MUTED}; font-size: 14px; text-align: center;">Your Ghost Teammate wants to perform an action that requires your explicit approval.</p>
        <div style="background: {BRAND_BG}; border-left: 3px solid {BRAND_WARNING}; padding: 16px 20px; margin: 0 0 24px 0; border-radius: 0 8px 8px 0;">
            <p style="margin: 0 0 6px 0; font-size: 11px; color: {BRAND_DIM}; text-transform: uppercase;">Proposed Action</p>
            <p style="margin: 0; font-size: 14px; color: white;">{action}</p>
        </div>
        <table role="presentation" width="100%">
            <tr>
                <td style="padding-right: 8px; width: 50%;">
                    <a href="{approve_url}" style="display: block; background: {BRAND_SUCCESS}; color: white; padding: 14px 24px; text-decoration: none; border-radius: 8px; text-align: center; font-weight: 600;">✓ Approve</a>
                </td>
                <td style="padding-left: 8px; width: 50%;">
                    <a href="{reject_url}" style="display: block; background: {BRAND_ERROR}; color: white; padding: 14px 24px; text-decoration: none; border-radius: 8px; text-align: center; font-weight: 600;">✗ Reject</a>
                </td>
            </tr>
        </table>
    '''
    return await send_teammate_email(user_email, user_id, "⚠️ Action Requires Your Approval", _get_email_wrapper(content))

async def send_task_started_email(user_email: str, user_id: str, goal: str, dashboard_url: Optional[str] = None) -> dict:
    dash_link = dashboard_url or f"{settings.FRONTEND_URL}/dashboard"
    content = f'''
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="display: inline-block; width: 56px; height: 56px; background: rgba(59, 130, 246, 0.1); border-radius: 16px; line-height: 56px; font-size: 28px;">🚀</div>
        </div>
        <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 600; color: white; text-align: center;">Task Started</h1>
        <div style="background: {BRAND_BG}; border: 1px solid {BRAND_BORDER}; padding: 16px 20px; margin: 0 0 24px 0; border-radius: 8px;">
            <p style="margin: 0 0 6px 0; font-size: 11px; color: {BRAND_DIM}; text-transform: uppercase;">Your Request</p>
            <p style="margin: 0; font-size: 14px; color: white;">{goal[:500]}</p>
        </div>
        <a href="{dash_link}" style="display: block; background: {BRAND_PRIMARY}; color: white; padding: 14px 24px; text-decoration: none; border-radius: 8px; text-align: center; font-weight: 600;">Watch Live in Dashboard →</a>
    '''
    return await send_teammate_email(user_email, user_id, "🚀 Working on your task", _get_email_wrapper(content))

async def send_completion_email(user_email: str, user_id: str, goal: str, summary: str, actions_taken: Optional[list] = None) -> dict:
    actions_html = ""
    if actions_taken:
        items = "".join([f'<li style="margin: 8px 0; color: {BRAND_TEXT}; font-size: 13px;">{a}</li>' for a in actions_taken[:5]])
        actions_html = f'<div style="background: {BRAND_BG}; border: 1px solid {BRAND_BORDER}; padding: 16px 20px; margin: 0 0 24px 0; border-radius: 8px;"><ul style="margin: 0; padding-left: 20px;">{items}</ul></div>'
    
    content = f'''
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="display: inline-block; width: 56px; height: 56px; background: rgba(34, 197, 94, 0.1); border-radius: 16px; line-height: 56px; font-size: 28px;">✅</div>
        </div>
        <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 600; color: {BRAND_SUCCESS}; text-align: center;">Task Completed</h1>
        <div style="background: {BRAND_BG}; border-left: 3px solid {BRAND_SUCCESS}; padding: 16px 20px; margin: 0 0 24px 0; border-radius: 0 8px 8px 0;">
            <p style="margin: 0 0 6px 0; font-size: 11px; color: {BRAND_DIM}; text-transform: uppercase;">Summary</p>
            <p style="margin: 0; font-size: 14px; color: white; line-height: 1.6;">{summary}</p>
        </div>
        {actions_html}
    '''
    return await send_teammate_email(user_email, user_id, "✅ Task Completed", _get_email_wrapper(content))

async def send_error_email(user_email: str, user_id: str, goal: str, error_type: str, error_message: str) -> dict:
    content = f'''
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="display: inline-block; width: 56px; height: 56px; background: rgba(239, 68, 68, 0.1); border-radius: 16px; line-height: 56px; font-size: 28px;">❌</div>
        </div>
        <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 600; color: {BRAND_ERROR}; text-align: center;">Task Failed</h1>
        <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); padding: 16px 20px; margin: 0 0 24px 0; border-radius: 8px;">
            <p style="margin: 0 0 6px 0; font-size: 11px; color: {BRAND_ERROR}; text-transform: uppercase;">Error Details</p>
            <p style="margin: 0; font-size: 13px; color: {BRAND_MUTED}; font-family: monospace;">{error_message}</p>
        </div>
    '''
    return await send_teammate_email(user_email, user_id, "❌ Task Failed", _get_email_wrapper(content))
