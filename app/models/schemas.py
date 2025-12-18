"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class EnhancementType(str, Enum):
    """Video enhancement types"""
    UPSCALE = "upscale"
    DENOISE = "denoise"
    COLOR_CORRECTION = "color_correction"
    STABILIZATION = "stabilization"
    SUPER_RESOLUTION = "super_resolution"
    MOTION_BLUR_REMOVAL = "motion_blur_removal"


class EditOperation(BaseModel):
    """Single video edit operation"""
    operation_type: str = Field(..., description="Type: trim, crop, rotate, resize, etc.")
    start_time: Optional[float] = Field(None, description="Start time in seconds")
    end_time: Optional[float] = Field(None, description="End time in seconds")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific parameters")


class VideoProcessRequest(BaseModel):
    """Request for video processing"""
    video_id: str = Field(..., description="Uploaded video ID")
    operations: List[EditOperation] = Field(..., description="List of editing operations")
    output_format: str = Field(default="mp4", description="Output video format")


class EnhancementSettings(BaseModel):
    """Settings for video enhancement"""
    intensity: float = Field(default=0.7, ge=0.0, le=1.0, description="Enhancement intensity (0-1)")
    preserve_quality: bool = Field(default=True, description="Preserve original quality")
    custom_params: Dict[str, Any] = Field(default_factory=dict, description="Custom parameters")


class VideoEnhancementRequest(BaseModel):
    """Request for video enhancement"""
    video_id: str = Field(..., description="Uploaded video ID")
    enhancement_type: EnhancementType = Field(..., description="Type of enhancement")
    settings: EnhancementSettings = Field(default_factory=EnhancementSettings)


class VideoMetadata(BaseModel):
    """Video metadata"""
    video_id: str
    filename: str
    duration: float
    width: int
    height: int
    fps: float
    file_size_mb: float
    codec: str
    status: str


class APIResponse(BaseModel):
    """Standard API response"""
    status: str = Field(..., description="Response status: success, error, processing")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: Optional[str] = Field(None, description="Response timestamp")


class Operation(BaseModel):
    """Single operation produced by instruction parsing"""
    type: str = Field(..., description="Operation type, e.g. denoise, stabilize, crop")
    params: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific parameters")


class InstructionRequest(BaseModel):
    """Request schema for instruction-driven editing"""
    video_id: str = Field(..., description="Uploaded video ID to operate on")
    instruction: str = Field(..., description="Natural language instruction for the AI to interpret")


class InstructionResponse(BaseModel):
    status: str = Field(...)
    operations: List[Operation] = Field(default_factory=list)
