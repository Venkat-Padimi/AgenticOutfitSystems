import sys
from pathlib import Path

# Ensure backend directory is in sys.path regardless of launch directory
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Re-export FastAPI app from backend/main.py to support both `main:app` and `app.main:app`
from main import app

__all__ = ["app"]
