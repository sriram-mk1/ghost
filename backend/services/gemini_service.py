import google.generativeai as genai
from backend.core.config import get_settings

settings = get_settings()
genai.configure(api_key=settings.GEMINI_API_KEY)

def get_model(model_name: str = "gemini-1.5-flash"):
    return genai.GenerativeModel(model_name)

