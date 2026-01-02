"""Application configuration"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    environment: str = "development"
    api_title: str = "Filmy AI - Video Editing & Enhancement API"
    api_version: str = "0.1.0"

    # Video Processing
    max_video_size_mb: int = 500
    supported_formats: str = "mp4,avi,mov,mkv,flv"
    temp_video_dir: str = "./data/temp_videos"
    output_video_dir: str = "./data/output_videos"
    
    # Video Encoding (Memory Optimization)
    video_preset: str = "medium"  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower
    video_bitrate: str = "2000k"  # Lower bitrate = less RAM usage (e.g., "1500k", "2000k", "3000k")
    video_crf: int = 28  # Quality (0-51, default 23: lower=better, higher=faster/smaller)
    audio_chunk_duration: float = 5.0  # Process audio in chunks (seconds) to reduce RAM

    # Database
    database_url: str = "sqlite:///./data/filmy_ai.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # AI Models
    model_device: str = "cuda"
    model_cache_dir: str = "./models"
    enable_gpu: bool = True

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    api_key: Optional[str] = None
    # Gemini / Generative Language API key (read from .env or environment)
    gemini_api_key: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = "utf-8-sig"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
