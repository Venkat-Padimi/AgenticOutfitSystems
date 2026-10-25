import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env file from backend root or parent
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseModel):
    app_name: str = "AI Personal Outfit Styling & Shopping Agent"
    version: str = "1.0.0"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    serpapi_api_key: str = os.getenv("SERPAPI_API_KEY", "")
    provider_mode: str = os.getenv("SHOPPING_PROVIDER_MODE", "hybrid")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
    agent_timeout_seconds: float = float(os.getenv("AGENT_TIMEOUT_SECONDS", "60.0"))
    agent_max_iterations: int = int(os.getenv("AGENT_MAX_ITERATIONS", "6"))

settings = Settings()
