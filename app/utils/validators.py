"""Input validation utilities"""

from typing import List
import os


def validate_video_file(file_path: str, allowed_extensions: List[str]) -> bool:
    """Validate if file is a supported video format"""
    if not os.path.exists(file_path):
        return False
    
    ext = os.path.splitext(file_path)[1].lower().strip(".")
    return ext in allowed_extensions


def validate_file_size(file_path: str, max_size_mb: int) -> bool:
    """Validate file size"""
    if not os.path.exists(file_path):
        return False
    
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    return file_size_mb <= max_size_mb


def get_file_extension(file_path: str) -> str:
    """Get file extension"""
    return os.path.splitext(file_path)[1].lower().strip(".")
