import resend
from backend.core.config import get_settings

settings = get_settings()
resend.api_key = settings.RESEND_API_KEY

def send_approval_email(to_email: str, workflow_id: str, action_description: str):
    # Construct an email with approval/rejection links
    # These links should point to our /webhooks/resend endpoint
    params = {
        "from": "Ghost Teammate <assistant@yourdomain.com>",
        "to": [to_email],
        "subject": "Approval Needed: Ghost Teammate Task",
        "html": f"""
            <p>Your Ghost Teammate needs approval for the following action:</p>
            <p><strong>{action_description}</strong></p>
            <a href="https://api.yourdomain.com/approve?id={workflow_id}">Approve</a>
            <a href="https://api.yourdomain.com/reject?id={workflow_id}">Reject</a>
        """,
    }
    return resend.Emails.send(params)

