"""
Supermemory Service
-------------------
Handles long-term memory for the Ghost Teammate.
Supermemory provides semantic search and user profiling
that persists across sessions.

API Reference: https://supermemory.ai/docs
"""
import os
from typing import Optional, Dict, Any, List
from backend.core.config import get_settings

settings = get_settings()

# Lazy-load the Supermemory client
_client = None


def _get_client():
    """
    Lazy-load the Supermemory client.
    Only initializes if API key is provided.
    """
    global _client
    if _client is None and settings.SUPERMEMORY_API_KEY:
        try:
            from supermemory import Supermemory
            _client = Supermemory(api_key=settings.SUPERMEMORY_API_KEY)
            print("✅ Supermemory client initialized")
        except ImportError:
            print("⚠️ Supermemory SDK not installed. Run: pip install supermemory")
        except Exception as e:
            print(f"⚠️ Failed to initialize Supermemory: {e}")
    return _client


def get_user_context(user_id: str, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches the user's profile and optionally relevant memories.
    
    The profile includes:
    - static: Facts that rarely change (name, job, preferences)
    - dynamic: Recent patterns and behaviors
    
    If a query is provided, also returns relevant memories.
    
    Args:
        user_id: Unique user identifier (used as container_tag)
        query: Optional search query for relevant context
        
    Returns:
        Dict with profile data and optional search results
    """
    client = _get_client()
    
    if client is None:
        # Return empty context if no Supermemory
        return {
            "user_id": user_id,
            "static": [],
            "dynamic": [],
            "memories": []
        }
    
    try:
        # Use the profile endpoint which combines profile + search
        profile_args = {"container_tag": user_id}
        if query:
            profile_args["q"] = query
        
        result = client.profile(**profile_args)
        
        # Extract profile data
        profile_data = {
            "user_id": user_id,
            "static": getattr(result.profile, 'static', []) if hasattr(result, 'profile') else [],
            "dynamic": getattr(result.profile, 'dynamic', []) if hasattr(result, 'profile') else [],
            "memories": []
        }
        
        # Extract search results if query was provided
        if query and hasattr(result, 'search_results') and result.search_results:
            profile_data["memories"] = [
                {
                    "content": r.content if hasattr(r, 'content') else str(r),
                    "score": getattr(r, 'score', 0)
                }
                for r in result.search_results.results[:5]
            ]
        
        return profile_data
        
    except Exception as e:
        print(f"⚠️ Failed to fetch user context: {e}")
        return {
            "user_id": user_id,
            "static": [],
            "dynamic": [],
            "memories": []
        }


def search_knowledge(query: str, user_id: str, limit: int = 5) -> str:
    """
    Searches the user's memory for relevant information.
    Used by the agent to check if it can answer from context.
    
    Args:
        query: What to search for
        user_id: User's container tag
        limit: Max results to return
        
    Returns:
        Formatted string of relevant memories
    """
    client = _get_client()
    
    if client is None:
        return "No memory context available."
    
    try:
        # Use the search endpoint
        results = client.search.execute(
            q=query,
            container_tags=[user_id],  # Must be a list
            limit=limit,
            rerank=True  # Use reranking for better relevance
        )
        
        if not results or not hasattr(results, 'results') or not results.results:
            return "No relevant memories found."
        
        # Format results for the agent
        memories = []
        for r in results.results[:limit]:
            content = r.content if hasattr(r, 'content') else str(r)
            score = getattr(r, 'score', 0)
            memories.append(f"[{score:.2f}] {content}")
        
        return "\n".join(memories)
        
    except Exception as e:
        print(f"⚠️ Memory search failed: {e}")
        return "Memory search unavailable."


def add_memory(user_id: str, content: str, metadata: Optional[Dict] = None) -> bool:
    """
    Stores a new memory for the user.
    Called after task completion to remember context.
    
    Args:
        user_id: User's container tag
        content: The memory content to store
        metadata: Optional metadata (type, source, etc.)
        
    Returns:
        True if memory was added successfully
    """
    client = _get_client()
    
    if client is None:
        return False
    
    try:
        client.add(
            content=content,
            container_tag=user_id,
            metadata=metadata or {}
        )
        print(f"📝 Memory added for user {user_id[:8]}...")
        return True
        
    except Exception as e:
        print(f"⚠️ Failed to add memory: {e}")
        return False


def add_conversation(user_id: str, messages: List[Dict[str, str]]) -> bool:
    """
    Stores a conversation for future context.
    
    Args:
        user_id: User's container tag
        messages: List of {"role": "user/assistant", "content": "..."}
        
    Returns:
        True if conversation was stored
    """
    # Format conversation as text
    formatted = "\n".join([
        f"{m['role']}: {m['content']}" 
        for m in messages
    ])
    
    return add_memory(
        user_id=user_id,
        content=formatted,
        metadata={"type": "conversation"}
    )


def format_context_for_agent(user_id: str, goal: str) -> str:
    """
    Builds a formatted context string for the agent.
    Combines profile + relevant memories.
    
    Args:
        user_id: User identifier
        goal: Current task goal for context search
        
    Returns:
        Formatted context string for system prompt
    """
    context = get_user_context(user_id, query=goal)
    
    parts = []
    
    # Add static profile facts
    if context.get("static"):
        parts.append("USER PROFILE:")
        for fact in context["static"]:
            parts.append(f"  • {fact}")
    
    # Add dynamic patterns
    if context.get("dynamic"):
        parts.append("\nRECENT PATTERNS:")
        for pattern in context["dynamic"]:
            parts.append(f"  • {pattern}")
    
    # Add relevant memories
    if context.get("memories"):
        parts.append("\nRELEVANT CONTEXT:")
        for mem in context["memories"]:
            content = mem.get("content", str(mem))
            parts.append(f"  • {content[:200]}...")
    
    if not parts:
        return "No prior context available for this user."
    
    return "\n".join(parts)
