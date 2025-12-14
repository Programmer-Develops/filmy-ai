"""API route definitions"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, WebSocket
from fastapi.responses import FileResponse
import os
import asyncio

from app.services.video_service import VideoService
from app.models.schemas import VideoProcessRequest, VideoEnhancementRequest, InstructionRequest
from app.config import get_settings

router = APIRouter(prefix="/api/v1", tags=["video-operations"])

# Initialize the AI Service
video_service = VideoService()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Filmy AI API",
        "version": "0.2.0 (AI Enabled)"
    }


@router.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file"""
    try:
        # Validate file type
        allowed_types = ["video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo", "application/octet-stream"]
        if file.content_type not in allowed_types:
            # Log warning but allow for now if needed, or stricter check
            pass

        settings = get_settings()
        file_path = await video_service.save_upload(file, settings.temp_video_dir)
        video_id = os.path.basename(file_path)

        return {
            "status": "success",
            "video_id": video_id,
            "message": f"Video uploaded successfully: {file.filename}",
            "filename": video_id 
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instruct")
async def instruct(request: InstructionRequest):
    """
    Accept a natural-language instruction, interpret it using Gemini, and execute edits.
    Waits for completion to return the output path directly.
    """
    try:
        settings = get_settings()
        video_path = os.path.join(settings.temp_video_dir, request.video_id)
        
        if not os.path.exists(video_path):
             raise HTTPException(status_code=404, detail=f"Video {request.video_id} not found in temp storage.")

        # Call the new AI-driven method in video_service
        # This will block until processing is done (good for demo, use BackgroundTasks for production)
        result = await video_service.edit_video_by_instruction(video_path, request.instruction)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_video(filename: str):
    """Download processed video"""
    settings = get_settings()
    out_dir = settings.output_video_dir
    file_path = os.path.join(out_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="video/mp4"
    )

# --- Legacy Endpoints (Optional / Backward Compatibility) ---

@router.post("/enhance/video")
async def enhance_video(request: VideoEnhancementRequest):
    """Legacy endpoint wrapper for AI enhancement"""
    try:
        settings = get_settings()
        video_path = os.path.join(settings.temp_video_dir, request.video_id)
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video not found")

        result = await video_service.enhance_video(video_path, request.enhancement_type, request.settings)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))