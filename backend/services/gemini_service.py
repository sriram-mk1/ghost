from google import genai
from backend.core.config import get_settings

settings = get_settings()
genai.configure(api_key=settings.GEMINI_API_KEY)

def get_agent_response(prompt: str, screenshot_bytes: bytes = None, model_name: str = "gemini-3-flash"):
    """
    Multimodal reasoning. If a screenshot is provided, Gemini will be able to view the Steel headless browser.
    """
    model = genai.GenerativeModel(model_name)

    content = [prompt]
    if screenshot_bytes:
        content.append({
            "mime_type": "image/png",
            "data": screenshot_bytes
        })

    response = model.generate_contetn(content)
    return response.text

