import sys
from pathlib import Path

# Ensure backend directory is in sys.path regardless of launch directory
backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers.agent import router as agent_router
from app.routers.shopping import router as shopping_router
from app.routers.blend import router as blend_router

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Backend API and Agent Orchestrator for AI Personal Outfit Styling & Shopping Agent ('Blend')"
)

# Configure CORS for React Native (Expo Go / Web / Emulator / Production)
origins = settings.cors_origins
is_wildcard = "*" in origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=not is_wildcard,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(agent_router)
app.include_router(shopping_router)
app.include_router(blend_router)

@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "version": settings.version,
        "docs_url": "/docs",
        "status": "operational"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "provider_mode": settings.provider_mode,
        "serpapi_configured": bool(settings.serpapi_api_key),
        "gemini_configured": bool(settings.gemini_api_key)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
