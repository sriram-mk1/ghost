from steel import Steel
from backend.core.config import get_settings

settings = get_settings()
steel_client = Steel(api_key=settings.STEEL_API_KEY)

async def start_teammate_browser(user_id: str, existing_session_id: str = None):
    "Manages the agent's browser session"
    if existing_session_id:
        try:
            return await steel_client.sessions.get(existing_session_id)
        except:
            pass # Session expired or doesn't exist

    # Create a new sesison with high stealth and residential proxy
    return await steel_client.sessions.create(
        use_proxy=True,
        stealth=True,
    )
    
