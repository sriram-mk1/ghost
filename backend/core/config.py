from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    
    TEMPORAL_ADDRESS: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    
    RESEND_API_KEY: str
    RESEND_WEBHOOK_SECRET: str
    
    STEEL_API_KEY: str
    STEEL_CONNECT_URL: str
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

