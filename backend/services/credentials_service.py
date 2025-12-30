"""
Credentials Service
-------------------
Manages the agent's credentials for signing into websites.

Steel provides:
1. Encrypted credential storage (username, password, TOTP)
2. Automatic form detection and injection
3. Session context capture and reuse

This service handles:
- Storing agent credentials securely in Steel
- Generating unique agent emails for each user
- Capturing and persisting auth state across sessions
"""
import secrets
import string
from typing import Optional, Dict, Any
from backend.core.config import get_settings
from backend.services.supabase_client import get_supabase
from backend.services.steel_service import steel_client

settings = get_settings()

# Agent email domain (must be verified in your email provider)
# Agent email domain (must be verified in your email provider)
AGENT_EMAIL_DOMAIN = "reluit.com"


def generate_agent_email(user_id: str, platform: str) -> str:
    """
    Generates a unique email for the agent per user+platform.
    
    Format: agent-{user_id_short}-{platform}@domain.com
    Example: agent-abc123-notion@ghost-teammate.com
    """
    short_id = user_id[:8] if len(user_id) > 8 else user_id
    platform_slug = platform.lower().replace(" ", "-")[:10]
    return f"agent-{short_id}-{platform_slug}@{AGENT_EMAIL_DOMAIN}"


def generate_secure_password(length: int = 24) -> str:
    """
    Generates a cryptographically secure password for agent accounts.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def store_credential_in_steel(
    origin: str,
    username: str,
    password: str,
    namespace: str = "ghost-teammate",
    totp_secret: Optional[str] = None
) -> Dict[str, Any]:
    """
    Stores credentials in Steel's encrypted credential vault.
    
    Steel will automatically detect login forms and inject these
    credentials when the agent navigates to the origin.
    
    Args:
        origin: Website origin (e.g., "https://notion.so")
        username: Agent's username/email for this site
        password: Agent's password
        namespace: Separates credentials by use case
        totp_secret: Optional TOTP secret for 2FA
        
    Returns:
        Credential storage result with ID
    """
    credential_data = {
        "origin": origin,
        "value": {
            "username": username,
            "password": password
        },
        "namespace": namespace
    }
    
    if totp_secret:
        credential_data["value"]["totpSecret"] = totp_secret
    
    try:
        result = steel_client.credentials.create(**credential_data)
        print(f"🔐 Stored credentials for {origin}")
        return {"id": result.id, "origin": origin, "status": "stored"}
    except Exception as e:
        print(f"⚠️ Failed to store credentials: {e}")
        return {"error": str(e), "status": "failed"}


async def create_agent_account(
    user_id: str,
    platform: str,
    platform_url: str,
    custom_password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates and stores credentials for the agent to use on a platform.
    
    This generates:
    - A unique agent email for this user+platform
    - A secure password (or uses provided one)
    - Stores in Steel for auto-injection
    - Stores in Supabase for reference
    
    Args:
        user_id: User who owns this agent
        platform: Platform name (e.g., "Notion", "Linear")
        platform_url: Base URL (e.g., "https://notion.so")
        custom_password: Optional pre-set password
        
    Returns:
        Account details (email visible, password hidden)
    """
    supabase = get_supabase()
    
    # Generate credentials
    agent_email = generate_agent_email(user_id, platform)
    agent_password = custom_password or generate_secure_password()
    
    # Store in Steel for auto-injection
    steel_result = await store_credential_in_steel(
        origin=platform_url,
        username=agent_email,
        password=agent_password,
        namespace=f"user-{user_id[:8]}"
    )
    
    # Store reference in Supabase (password NOT stored here, only in Steel)
    workspace_data = {
        "user_id": user_id,
        "platform_name": platform,
        "agent_email": agent_email,
        "credentials_vault_id": steel_result.get("id"),
        "is_active": True
    }
    
    # Upsert to handle duplicates
    result = supabase.table("workspaces").upsert(
        workspace_data,
        on_conflict="user_id,platform_name"
    ).execute()
    
    return {
        "platform": platform,
        "agent_email": agent_email,
        "status": "created",
        "note": "Password securely stored in Steel. Agent will auto-login."
    }


async def get_agent_credentials(user_id: str, platform: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the agent's credentials for a platform.
    
    Note: Returns email only. Password is stored in Steel and
    injected automatically during browser sessions.
    """
    supabase = get_supabase()
    
    result = supabase.table("workspaces").select("*").eq(
        "user_id", user_id
    ).eq(
        "platform_name", platform
    ).single().execute()
    
    if result.data:
        return {
            "platform": result.data["platform_name"],
            "agent_email": result.data["agent_email"],
            "is_active": result.data["is_active"]
        }
    
    return None


async def capture_session_auth(session_id: str) -> Dict[str, Any]:
    """
    Captures the current authentication state from a Steel session.
    
    This includes cookies, localStorage, and session data.
    Can be reused to create new sessions that are already logged in.
    
    Returns:
        Session context object that can be passed to new sessions
    """
    try:
        context = steel_client.sessions.context(session_id)
        print(f"📸 Captured auth context from session {session_id[:8]}...")
        return {
            "context": context,
            "status": "captured"
        }
    except Exception as e:
        print(f"⚠️ Failed to capture session context: {e}")
        return {"error": str(e), "status": "failed"}


async def create_authenticated_session(
    user_id: str,
    session_context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Creates a new Steel session with pre-loaded authentication.
    
    If session_context is provided, the session will start already
    logged in to previously authenticated sites.
    
    Args:
        user_id: User identifier (for credential namespace)
        session_context: Previously captured auth context
        
    Returns:
        Session info with id and viewer URL
    """
    session_params = {
        "use_proxy": True,
        "solve_captcha": True,
        "session_timeout": 1800000,  # 30 min
        "dimensions": {"width": 1280, "height": 768},
        "credentials_namespace": f"user-{user_id[:8]}"  # Match credentials
    }
    
    if session_context:
        session_params["session_context"] = session_context
    
    try:
        session = steel_client.sessions.create(**session_params)
        print(f"🖥️ Created authenticated session: {session.id}")
        
        return {
            "id": session.id,
            "session_viewer_url": session.session_viewer_url,
            "has_auth_context": session_context is not None
        }
    except Exception as e:
        print(f"⚠️ Failed to create session: {e}")
        raise


async def store_session_context_for_user(
    user_id: str,
    session_id: str
) -> bool:
    """
    Captures and stores session auth context in Supermemory.
    
    This allows the agent to resume authenticated sessions
    across different workflows.
    """
    from backend.services.supermemory_service import add_memory
    
    try:
        # Capture from Steel
        context_result = await capture_session_auth(session_id)
        
        if context_result.get("status") == "captured":
            # Store in Supermemory (encrypted)
            import json
            context_json = json.dumps(context_result["context"])
            
            add_memory(
                user_id=user_id,
                content=f"SESSION_CONTEXT: {context_json[:500]}...",  # Truncate for storage
                metadata={
                    "type": "session_context",
                    "session_id": session_id
                }
            )
            
            return True
    except Exception as e:
        print(f"⚠️ Failed to store session context: {e}")
    
    return False

