from supermemory import SuperMemory
from backend.core.config import get_settings

settings = get_settings()
# Init for the new Supermemory SDK
sm = SuperMemory(api_key=settings.SUPERMEMORY_API_KEY)

def get_user_context(user_id: str):
    """Fetches the user prefernces, habits, and persona based on user id"""
    # Allowing the agent to know the user before every turn
    return sm.get_user_profile(user_id=user_id)

def search_knowledge(query:str, user_id: str):
    """Searches the user's knowledge base for relevant information"""
    return sm.search(query=query, user_id=user_id)