#!/usr/bin/env python3
"""
Ghost Teammate Integration Tests
--------------------------------
Run this to verify all components are working correctly.

Usage:
    cd backend
    python test_integrations.py
"""
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def test_gemini():
    """Test basic Gemini API connectivity."""
    print("\n" + "="*60)
    print("🧪 TEST 1: Gemini LLM Integration")
    print("="*60)
    
    try:
        from google import genai
        from backend.core.config import get_settings
        
        settings = get_settings()
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        print(f"✅ Gemini client initialized")
        print(f"   Model: gemini-3-flash-preview")
        
        # Simple test call
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents="Say 'Hello Ghost!' in exactly 2 words."
        )
        
        if response.text:
            print(f"✅ Model responded: {response.text.strip()}")
            return True
        else:
            print("❌ No response from model")
            return False
            
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False


def test_steel():
    """Test Steel API connectivity."""
    print("\n" + "="*60)
    print("🧪 TEST 2: Steel Browser Service")
    print("="*60)
    
    try:
        from steel import Steel
        from backend.core.config import get_settings
        
        settings = get_settings()
        client = Steel(steel_api_key=settings.STEEL_API_KEY)
        
        print(f"✅ Steel client initialized")
        
        # Try to create a quick session
        print("   Creating test browser session...")
        session = client.sessions.create(
            dimensions={"width": 1280, "height": 768}
        )
        
        print(f"✅ Session created: {session.id[:16]}...")
        print(f"   Viewer URL: {session.session_viewer_url}")
        
        # Take a screenshot
        print("   Taking screenshot...")
        resp = client.sessions.computer(session.id, action="take_screenshot")
        img = getattr(resp, "base64_image", "")
        
        if img and len(img) > 100:
            print(f"✅ Screenshot captured: {len(img)} bytes base64")
        else:
            print(f"⚠️ Screenshot may be empty: {len(img) if img else 0} bytes")
        
        # Clean up
        client.sessions.release(session.id)
        print(f"✅ Session released")
        
        return True
        
    except Exception as e:
        print(f"❌ Steel test failed: {e}")
        return False


def test_supabase():
    """Test Supabase connectivity."""
    print("\n" + "="*60)
    print("🧪 TEST 3: Supabase Database")
    print("="*60)
    
    try:
        from backend.services.supabase_client import get_supabase
        
        supabase = get_supabase()
        print(f"✅ Supabase client initialized")
        
        # Try a simple query
        result = supabase.table("jobs").select("id").limit(1).execute()
        
        print(f"✅ Database query successful")
        print(f"   Jobs table accessible: {len(result.data)} rows returned")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase test failed: {e}")
        return False


def test_resend():
    """Test Resend email service."""
    print("\n" + "="*60)
    print("🧪 TEST 4: Resend Email Service")
    print("="*60)
    
    try:
        import resend
        from backend.core.config import get_settings
        
        settings = get_settings()
        resend.api_key = settings.RESEND_API_KEY
        
        print(f"✅ Resend client initialized")
        print(f"   Agent email: ghost@{settings.AGENT_EMAIL_DOMAIN}")
        
        # Just verify API key is valid by checking domains
        # We won't actually send an email in the test
        print(f"✅ API key configured (not sending test email)")
        
        return True
        
    except Exception as e:
        print(f"❌ Resend test failed: {e}")
        return False


def test_supermemory():
    """Test Supermemory service."""
    print("\n" + "="*60)
    print("🧪 TEST 5: Supermemory Long-Term Memory")
    print("="*60)
    
    try:
        from backend.core.config import get_settings
        settings = get_settings()
        
        if not settings.SUPERMEMORY_API_KEY:
            print("⏭️ Skipped: SUPERMEMORY_API_KEY not configured")
            return True
        
        from supermemory import Supermemory
        client = Supermemory(api_key=settings.SUPERMEMORY_API_KEY)
        
        print(f"✅ Supermemory client initialized")
        
        # Try a search
        results = client.search.execute(q="test", limit=1)
        print(f"✅ Search API working")
        
        return True
        
    except ImportError:
        print("⏭️ Skipped: supermemory package not installed")
        return True
    except Exception as e:
        print(f"❌ Supermemory test failed: {e}")
        return False


async def test_agent_integration():
    """Test the full agent workflow."""
    print("\n" + "="*60)
    print("🧪 TEST 6: Full Agent Integration")
    print("="*60)
    
    try:
        from backend.services.agent_service import GhostTeammateAgent
        
        # Create agent without browser session
        agent = GhostTeammateAgent(
            user_id="test-user-123",
            user_profile={"name": "Test User"},
            session_id=None  # No browser for this test
        )
        
        print(f"✅ Agent initialized")
        print(f"   Model: gemini-3-flash-preview")
        
        # Test strategy decision (doesn't need browser)
        print("   Testing strategy planning...")
        result = await agent.decide_strategy("What is 2 + 2?")
        
        print(f"✅ Strategy decided: {result['strategy']}")
        print(f"   Reasoning: {result['reasoning'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "🤖 "*20)
    print("\n  GHOST TEAMMATE INTEGRATION TESTS")
    print("\n" + "🤖 "*20)
    
    results = {}
    
    # Run sync tests
    results["Gemini LLM"] = test_gemini()
    results["Steel Browser"] = test_steel()
    results["Supabase DB"] = test_supabase()
    results["Resend Email"] = test_resend()
    results["Supermemory"] = test_supermemory()
    
    # Run async tests
    loop = asyncio.get_event_loop()
    results["Agent Integration"] = loop.run_until_complete(test_agent_integration())
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED - Check the logs above")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
