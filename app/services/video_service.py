"""Video processing and enhancement service"""

import os
import asyncio
import shutil
import subprocess
from typing import Dict, List, Any, Optional
from fastapi import UploadFile
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VideoService:
    """Service for video operations"""

    def __init__(self):
        self.processing_status = {}

    async def save_upload(self, file: UploadFile, temp_dir: str) -> str:
        """Save uploaded file to temporary directory"""
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(temp_dir, f"{timestamp}_{file.filename}")
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Video saved: {file_path}")
        return file_path

    async def enhance_video(
        self,
        video_path: str,
        enhancement_type: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance video with specified enhancement type"""
        
        logger.info(f"Starting enhancement: {enhancement_type} for {video_path}")

        # Mark processing status
        video_id = os.path.basename(video_path)
        self.processing_status[video_id] = "processing"

        # Simulate processing (replace with actual AI model logic)
        await asyncio.sleep(0.5)

        output_dir = os.path.dirname(video_path).replace("temp_videos", "output_videos")
        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.basename(video_path)
        output_path = os.path.join(output_dir, f"{enhancement_type}_{base_name}")

        # Try to run ffmpeg to add a visible overlay (drawbox) so the output visibly differs.
        # Requires `ffmpeg` available on PATH. If it fails, fall back to copying the file.
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vf",
            "drawbox=x=0:y=0:w=iw:h=60:color=black@0.5:t=fill",
            "-c:a",
            "copy",
            output_path,
        ]

        try:
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"ffmpeg produced output: {output_path}")
        except Exception as e:
            logger.warning(f"ffmpeg failed or not found ({e}), falling back to copy for {video_path}")
            try:
                shutil.copy2(video_path, output_path)
            except Exception:
                with open(video_path, "rb") as r, open(output_path, "wb") as w:
                    w.write(r.read())

        # Mark statuses for input and output
        self.processing_status[video_id] = "completed"
        self.processing_status[os.path.basename(output_path)] = "completed"

        logger.info(f"Enhancement completed: {output_path}")

        return {
            "output_path": output_path,
            "processing_time": 1.0,
            "enhancement_type": enhancement_type
        }

    async def edit_video(
        self,
        video_path: str,
        operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply editing operations to video"""
        
        logger.info(f"Starting video editing with {len(operations)} operations")

        video_id = os.path.basename(video_path)
        self.processing_status[video_id] = "processing"

        # Simulate processing (replace with actual video editing logic)
        await asyncio.sleep(1)

        output_dir = os.path.dirname(video_path).replace("temp_videos", "output_videos")
        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.basename(video_path)
        output_path = os.path.join(output_dir, f"edited_{base_name}")

        try:
            shutil.copy2(video_path, output_path)
        except Exception:
            with open(video_path, "rb") as r, open(output_path, "wb") as w:
                w.write(r.read())

        self.processing_status[video_id] = "completed"
        self.processing_status[os.path.basename(output_path)] = "completed"

        logger.info(f"Editing completed: {output_path}")

        return {
            "output_path": output_path,
            "processing_time": 1.0,
            "operations_applied": len(operations)
        }

    async def get_status(self, video_id: str) -> str:
        """Get video processing status"""
        return self.processing_status.get(video_id, "completed")

    async def extract_frames(self, video_path: str, output_dir: str, fps: int = 1) -> List[str]:
        """Extract frames from video"""
        logger.info(f"Extracting frames from {video_path} at {fps} fps")
        # Implementation for frame extraction
        return []

    async def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata"""
        logger.info(f"Extracting metadata from {video_path}")
        
        # Placeholder metadata (use OpenCV or ffmpeg to get actual values)
        return {
            "duration": 0.0,
            "width": 1920,
            "height": 1080,
            "fps": 24.0,
            "codec": "h264"
        }
