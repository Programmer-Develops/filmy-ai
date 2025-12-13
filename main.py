"""Main application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from app.config import get_settings
from app.api.routes import router
from app.utils.logger import setup_logger

# Setup logger
logger = setup_logger("filmy-ai", level="INFO")


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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
