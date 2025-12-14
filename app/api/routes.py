"""API route definitions"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, WebSocket
from fastapi.responses import FileResponse
import os
import asyncio
from ..services.video_service import VideoService
from ..models.schemas import VideoProcessRequest, VideoEnhancementRequest, EnhancementType
from ..models.schemas import InstructionRequest, InstructionResponse
from ..services.instruction_service import interpret_and_enqueue, parse_instruction
from ..config import get_settings

router = APIRouter(prefix="/api/v1", tags=["video-operations"])

video_service = VideoService()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Filmy AI API",
        "version": "0.1.0"
    }


@router.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file"""
    try:
        # Validate file type
        allowed_types = ["video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not allowed. Supported: {allowed_types}"
            )

        settings = get_settings()
        file_path = await video_service.save_upload(file, settings.temp_video_dir)
        video_id = os.path.basename(file_path)

        return {
            "status": "success",
            "video_id": video_id,
            "message": f"Video uploaded successfully: {file.filename}",
            "size_mb": file.size / (1024 * 1024) if file.size else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance/video")
async def enhance_video(request: VideoEnhancementRequest):
    """Enhance a video with AI features"""
    try:
        settings = get_settings()
        video_path = os.path.join(settings.temp_video_dir, request.video_id)

        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video not found")

        # Apply enhancements based on type
        result = await video_service.enhance_video(
            video_path=video_path,
            enhancement_type=request.enhancement_type,
            settings=request.settings
        )

        return {
            "status": "success",
            "message": f"Video enhanced with {request.enhancement_type}",
            "output_path": result["output_path"],
            "processing_time": result.get("processing_time", "N/A")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edit/video")
async def edit_video(request: VideoProcessRequest):
    """Apply editing operations to a video"""
    try:
        settings = get_settings()
        video_path = os.path.join(settings.temp_video_dir, request.video_id)

        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video not found")

        result = await video_service.edit_video(
            video_path=video_path,
            operations=request.operations
        )

        return {
            "status": "success",
            "message": "Video edited successfully",
            "output_path": result["output_path"],
            "processing_time": result.get("processing_time", "N/A")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{video_id}")
async def download_video(video_id: str):
    """Download processed video"""
    settings = get_settings()
    out_dir = settings.output_video_dir
    file_path = os.path.join(out_dir, video_id)

    # If exact file doesn't exist, try to find a candidate that contains the id
    if not os.path.exists(file_path):
        if os.path.exists(out_dir):
            candidates = [f for f in os.listdir(out_dir) if video_id in f]
            if candidates:
                file_path = os.path.join(out_dir, candidates[0])
            else:
                raise HTTPException(status_code=404, detail="Video not found")
        else:
            raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="video/mp4"
    )


@router.get('/debug/outputs', tags=["debug"])
async def list_output_files():
    """Debug endpoint: list files in the output directory"""
    settings = get_settings()
    out_dir = settings.output_video_dir
    if not os.path.exists(out_dir):
        return {"output_dir": out_dir, "files": []}
    files = os.listdir(out_dir)
    return {"output_dir": out_dir, "files": files}


@router.get("/status/{video_id}")
async def get_video_status(video_id: str):
    """Get video processing status"""
    try:
        status = await video_service.get_status(video_id)
        return {
            "video_id": video_id,
            "status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instruct")
async def instruct(request: InstructionRequest, background_tasks: BackgroundTasks):
    """Accept a natural-language instruction, interpret it, and enqueue processing."""
    try:
        settings = get_settings()

        # simple processor that runs operations synchronously using video_service
        def _processor(video_id, operations):
            # This runs in background thread context when scheduled by FastAPI
            # Map simple operation types to existing video_service calls
            for op in operations:
                typ = op.get("type")
                params = op.get("params", {})
                video_path = os.path.join(settings.temp_video_dir, video_id)
                # quick mapping
                if typ in ("denoise", "upscale", "denoise_audio"):
                    # call enhance_video
                    # Note: video_service.enhance_video is async, but BackgroundTasks runs sync.
                    import asyncio as _asyncio
                    _asyncio.run(video_service.enhance_video(video_path, typ, params))
                elif typ in ("stabilize", "stabilization"):
                    import asyncio as _asyncio
                    _asyncio.run(video_service.enhance_video(video_path, "stabilization", params))
                else:
                    # fallback to edit_video with a minimal operation payload
                    import asyncio as _asyncio
                    _asyncio.run(video_service.edit_video(video_path, [op]))

        # interpret and enqueue
        operations = parse_instruction(request.instruction)
        background_tasks.add_task(_processor, request.video_id, operations)

        return {"status": "accepted", "operations": operations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket('/ws/progress/{video_id}')
async def ws_progress(websocket: WebSocket, video_id: str):
    """WebSocket endpoint that streams processing status for a video id."""
    await websocket.accept()
    try:
        while True:
            status = await video_service.get_status(video_id)
            await websocket.send_json({"video_id": video_id, "status": status})
            if status == "completed":
                break
            await asyncio.sleep(1.0)
    except Exception:
        pass
    finally:
        await websocket.close()
