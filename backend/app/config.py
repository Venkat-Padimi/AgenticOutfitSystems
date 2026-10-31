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
    debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1")
    agent_timeout_seconds: float = float(os.getenv("AGENT_TIMEOUT_SECONDS", "60.0"))
    agent_max_iterations: int = int(os.getenv("AGENT_MAX_ITERATIONS", "6"))
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "")
    database_url: str = os.getenv("DATABASE_URL", "")
    persistence_dir: str = os.getenv("PERSISTENCE_DIR", "")

    @property
    def cors_origins(self) -> list[str]:
        if not self.allowed_origins.strip():
            # Default safe origins for local web development and Expo previews
            return [
                "http://localhost:8081",
                "http://localhost:19006",
                "http://127.0.0.1:8081",
                "http://localhost:3000",
                "http://localhost:8000",
            ]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

settings = Settings()
