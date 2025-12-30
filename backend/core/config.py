from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv
from typing import Optional

# Explicitly load .env from the backend root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

class Settings(BaseSettings):
    """
    Central configuration for the Ghost Teammate backend.
    All values are loaded from the .env file in /backend/.env
    """
    # --- Gemini (Brain) ---
    GEMINI_API_KEY: str
    
    # --- Temporal (Durable Orchestration) ---
    TEMPORAL_ADDRESS: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    
    # --- Supabase (Database & Auth) ---
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    
    # --- Resend (Email Communication) ---
    RESEND_API_KEY: str
    RESEND_WEBHOOK_SECRET: str = ""  # Optional for local dev
    AGENT_EMAIL_DOMAIN: str = "reluit.com"  # Domain for ghost@domain.com
    
    # --- Steel (Virtual Computer) ---
    STEEL_API_KEY: str
    STEEL_CONNECT_URL: str = "wss://connect.steel.dev/"
    
    # --- Supermemory (Long-Term Memory) ---
    SUPERMEMORY_API_KEY: str = ""  # Optional if not using Supermemory
    
    # --- App URLs ---
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

@lru_cache()
def get_settings():
    return Settings()
