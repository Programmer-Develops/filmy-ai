import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the current directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.api.routes import router
from app.utils.logger import setup_logger

logger = setup_logger("filmy-ai", level="INFO")
logging.info(f"🎬 Filmy-AI started - If useful, please star: https://github.com/Programmer-Develops/filmy-ai")

FIRST_RUN_FILE = ".first_run"
if not os.path.exists(FIRST_RUN_FILE):
    print("\n" + "="*50)
    print("🎬 Thanks for trying Filmy-AI!")
    print("⭐ If this helps your project, consider starring:")
    print("   https://github.com/Programmer-Develops/filmy-ai")
    print("="*50 + "\n")
    with open(FIRST_RUN_FILE, 'w') as f:
        f.write("1")
        
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    # Startup
    logger.info("Starting Filmy AI API...")
    settings = get_settings()
    
    # Create necessary directories
    for dir_path in [
        settings.temp_video_dir,
        settings.output_video_dir,
        "./logs",
        settings.model_cache_dir
    ]:
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Directory ready: {dir_path}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Filmy AI API...")


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="AI-powered API for video editing and enhancement",
    lifespan=lifespan
)

# --- CORS CONFIGURATION (FIXED) ---
# When allow_credentials=True, you CANNOT use ["*"]. 
# You must list the specific origins that need access.
origins = [
    "http://127.0.0.1:5500",      # VS Code Live Server
    "http://localhost:5500",      # Alternative localhost
    "https://filmy-ai.onrender.com", # Production domain
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------------------

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "status": "running",
        "docs": "/docs"
    }

# --- FAVICON FIX ---
# Returns 204 No Content to silence the browser's 404 error for favicon
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(status_code=204)
# -------------------

@app.get("/api/v1/features")
async def get_features():
    """Get available features"""
    return {
        "video_enhancements": [
            "upscale",
            "denoise",
            "color_correction",
            "stabilization",
            "super_resolution",
            "motion_blur_removal"
        ],
        "editing_operations": [
            "trim",
            "crop",
            "rotate",
            "resize",
            "speed_adjust",
            "brightness_contrast"
        ],
        "supported_formats": settings.supported_formats.split(",")
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )