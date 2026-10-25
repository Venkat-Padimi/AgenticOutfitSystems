# Re-export FastAPI app from backend/main.py to support both `main:app` and `app.main:app`
from main import app

__all__ = ["app"]
