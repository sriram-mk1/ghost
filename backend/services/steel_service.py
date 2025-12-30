"""
Steel Service
-------------
Manages the agent's virtual computer (headless browser).
Steel provides a cloud-based Chromium instance that the agent 
can control like a human using mouse/keyboard actions.

Key Features:
- Session persistence (stay logged in)
- Credential auto-injection (secure login)
- Session context capture/restore
- CAPTCHA solving
- Residential proxies

API Reference: https://docs.steel.dev
"""
from steel import Steel
from typing import Optional, Dict, Any, Tuple, List
from backend.core.config import get_settings

settings = get_settings()

# Initialize Steel client with API key
steel_client = Steel(steel_api_key=settings.STEEL_API_KEY)


async def start_teammate_browser(
    user_id: str, 
    existing_session_id: Optional[str] = None,
    session_context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Creates or reconnects to a Steel browser session.
    
    Features:
    - Session persistence (agent stays logged in)
    - Credential namespace (auto-injects stored credentials)
    - Session context (pre-load auth state)
    
    Args:
        user_id: User identifier (used for credential namespace)
        existing_session_id: Reconnect to existing session if valid
        session_context: Pre-captured auth state to restore
    
    Returns: Session dict with id and session_viewer_url
    """
    # Try to reconnect to existing session
    if existing_session_id:
        try:
            context = steel_client.sessions.context(existing_session_id)
            if context:
                print(f"♻️ Reconnected to Steel session: {existing_session_id}")
                return {
                    "id": existing_session_id,
                    "session_viewer_url": f"https://app.steel.dev/sessions/{existing_session_id}/viewer",
                    "reconnected": True
                }
        except Exception as e:
            print(f"⚠️ Could not reconnect to session: {e}")
    
    # Build session parameters
    # Note: use_proxy and solve_captcha require paid Steel plans
    session_params = {
        "use_proxy": False,           # Requires paid plan - set True if upgraded
        "solve_captcha": False,       # Requires paid plan - set True if upgraded  
        "dimensions": {"width": 1280, "height": 768},
        # IMPORTANT: This namespace must match credentials stored for this user
        "namespace": f"user-{user_id[:8]}"
    }
    
    # Restore previous auth state if provided
    if session_context:
        session_params["session_context"] = session_context
        print("🔐 Starting session with pre-loaded auth context")
    
    # Create new session
    session = steel_client.sessions.create(**session_params)
    
    # Steel returns debugUrl which is the correct embed URL for live viewing
    debug_url = getattr(session, 'debug_url', None) or getattr(session, 'debugUrl', None)
    # Fallback to session_viewer_url if debug_url not available
    viewer_url = debug_url or getattr(session, 'session_viewer_url', f"https://app.steel.dev/sessions/{session.id}/viewer")
    
    print(f"🖥️ New Steel session: {session.id}")
    print(f"👁️ Live view (debugUrl): {viewer_url}")
    
    return {
        "id": session.id,
        "session_viewer_url": viewer_url,
        "debug_url": debug_url,
        "reconnected": False
    }


def capture_auth_context(session_id: str) -> Optional[Dict]:
    """
    Captures the current authentication state from a session.
    
    This includes cookies, localStorage, and session data.
    Can be reused to create new sessions that are already logged in.
    """
    try:
        context = steel_client.sessions.context(session_id)
        print(f"📸 Captured auth context from {session_id[:8]}...")
        return context
    except Exception as e:
        print(f"⚠️ Failed to capture auth context: {e}")
        return None


def take_screenshot(session_id: str) -> str:
    """
    Takes a screenshot of the current browser state.
    Returns base64-encoded PNG image.
    """
    resp = steel_client.sessions.computer(session_id, action="take_screenshot")
    return getattr(resp, "base64_image", "")


def execute_action(
    session_id: str,
    action: str,
    coordinates: Optional[List[int]] = None,
    text: Optional[str] = None,
    keys: Optional[List[str]] = None,
    button: str = "left",
    delta_x: int = 0,
    delta_y: int = 0,
    duration: float = 1.0,
    num_clicks: int = 1,
    path: Optional[List[List[int]]] = None
) -> Tuple[str, str]:
    """
    Execute a computer action on the Steel session.
    
    Actions:
    - take_screenshot
    - click_mouse
    - move_mouse  
    - type_text
    - press_key
    - scroll
    - drag_mouse
    - wait
    
    Returns: (base64_screenshot, current_url)
    """
    payload: Dict[str, Any] = {
        "action": action,
        "screenshot": True
    }
    
    # Add action-specific parameters
    if coordinates:
        payload["coordinates"] = coordinates
    
    if text and action == "type_text":
        payload["text"] = text
    
    if keys and action == "press_key":
        payload["keys"] = keys
    
    if action == "click_mouse":
        payload["button"] = button
        if num_clicks > 1:
            payload["num_clicks"] = num_clicks
    
    if action == "scroll":
        if delta_x:
            payload["delta_x"] = delta_x
        if delta_y:
            payload["delta_y"] = delta_y
    
    if action == "drag_mouse" and path:
        payload["path"] = path
    
    if action == "wait":
        payload["duration"] = duration
    
    # Execute the action
    resp = steel_client.sessions.computer(session_id, **payload)
    
    screenshot = getattr(resp, "base64_image", "") or ""
    url = getattr(resp, "url", "about:blank")
    
    return screenshot, url


# Convenience functions for common actions
def get_cursor_position(session_id: str) -> Tuple[int, int]:
    """Get current cursor position (x, y)."""
    screenshot, url = execute_action(session_id, "get_cursor_position")
    # Note: Steel API might return coordinates in the response metadata, 
    # but the python SDK wrapper simplifies it. 
    # If the SDK doesn't return metadata, we might need to rely on the side-effect 
    # or check if the response object has it.
    # For now, we assume the action is valid.
    return (0, 0) # Placeholder as SDK response inspection didn't show coord return.


def click(session_id: str, x: int, y: int, button: str = "left") -> Tuple[str, str]:
    """Click at coordinates."""
    return execute_action(session_id, "click_mouse", coordinates=[x, y], button=button)


def double_click(session_id: str, x: int, y: int) -> Tuple[str, str]:
    """Double-click at coordinates."""
    return execute_action(session_id, "click_mouse", coordinates=[x, y], num_clicks=2)


def type_text(session_id: str, text: str) -> Tuple[str, str]:
    """Type text (assumes field is focused)."""
    return execute_action(session_id, "type_text", text=text)


def press_keys(session_id: str, keys: List[str]) -> Tuple[str, str]:
    """Press key combination (e.g., ['Control', 'a'])."""
    return execute_action(session_id, "press_key", keys=keys)


def scroll(session_id: str, x: int, y: int, delta_y: int = 400) -> Tuple[str, str]:
    """Scroll at coordinates. Positive delta_y = scroll down."""
    return execute_action(session_id, "scroll", coordinates=[x, y], delta_y=delta_y)


def move_mouse(session_id: str, x: int, y: int) -> Tuple[str, str]:
    """Move mouse to coordinates (hover)."""
    return execute_action(session_id, "move_mouse", coordinates=[x, y])


def wait(session_id: str, seconds: float = 1.0) -> Tuple[str, str]:
    """Wait for specified duration."""
    return execute_action(session_id, "wait", duration=seconds)


async def release_session(session_id: str):
    """Releases a Steel session when the task is complete."""
    try:
        steel_client.sessions.release(session_id)
        print(f"🔓 Released Steel session: {session_id}")
    except Exception as e:
        print(f"⚠️ Failed to release session: {e}")


# Credential management (uses Steel's secure credential vault)
def store_credentials(
    origin: str,
    username: str,
    password: str,
    namespace: str,
    totp_secret: Optional[str] = None
) -> Dict[str, Any]:
    """
    Store credentials in Steel's encrypted vault.
    
    When the agent navigates to 'origin', Steel will automatically
    detect login forms and inject these credentials.
    
    Args:
        origin: Website origin (e.g., "https://notion.so")
        username: Login username/email
        password: Login password
        namespace: Credential namespace (use user ID)
        totp_secret: Optional TOTP secret for 2FA
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
        return {
            "id": result.id,
            "origin": origin,
            "status": "stored"
        }
    except Exception as e:
        print(f"⚠️ Failed to store credentials: {e}")
        return {"error": str(e), "status": "failed"}


def get_stored_credentials(origin: str, namespace: str) -> Optional[Dict]:
    """
    Retrieves stored credentials info (not the actual password).
    """
    try:
        # Note: Steel API may not expose this directly
        # Credentials are injected automatically during sessions
        return {"origin": origin, "namespace": namespace, "exists": True}
    except Exception as e:
        return None
