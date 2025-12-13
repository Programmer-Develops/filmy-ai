# Filmy AI - Getting Started Guide

## Overview
Filmy AI is a Python-based AI API for video editing and enhancement. It provides RESTful endpoints for:
- Video uploading and processing
- AI-powered video enhancement (upscaling, denoising, color correction, etc.)
- Video editing operations (trim, crop, rotate, etc.)
- Video downloading

## Prerequisites
- Python 3.10+
- FFmpeg (for video processing)
- pip (Python package manager)

### Install FFmpeg
**Windows:**
```powershell
choco install ffmpeg
# or download from https://ffmpeg.org/download.html
```

**Linux/macOS:**
```bash
# Linux
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

## Installation

### 1. Clone and Navigate to Project
```bash
cd c:\Users\Shantanu Pandya\Documents\myPack-or-API\filmy-ai
```

### 2. Create Virtual Environment
```bash
# Create venv
python -m venv venv

# Activate venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy example env
copy .env.example .env

# Edit .env with your settings (optional, defaults work fine for development)
```

### 5. Run API Server
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

### Interactive Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### 1. Health Check
```
GET /api/v1/health
```
Check if API is running.

#### 2. Upload Video
```
POST /api/v1/upload/video
```
Upload a video file.

**Request:**
- Multipart form with `file` field

**Response:**
```json
{
  "status": "success",
  "video_id": "20231213_120000_video.mp4",
  "message": "Video uploaded successfully",
  "size_mb": 150.5
}
```

#### 3. Enhance Video
```
POST /api/v1/enhance/video
```
Apply AI enhancement to video.

**Request:**
```json
{
  "video_id": "20231213_120000_video.mp4",
  "enhancement_type": "upscale",
  "settings": {
    "intensity": 0.8,
    "preserve_quality": true
  }
}
```

**Enhancement Types:**
- `upscale` - Upscale video to higher resolution
- `denoise` - Remove noise from video
- `color_correction` - Automatic color correction
- `stabilization` - Video stabilization
- `super_resolution` - Super resolution enhancement
- `motion_blur_removal` - Remove motion blur

#### 4. Edit Video
```
POST /api/v1/edit/video
```
Apply editing operations to video.

**Request:**
```json
{
  "video_id": "20231213_120000_video.mp4",
  "operations": [
    {
      "operation_type": "trim",
      "start_time": 5.0,
      "end_time": 30.0
    },
    {
      "operation_type": "crop",
      "parameters": {
        "x": 100,
        "y": 100,
        "width": 1280,
        "height": 720
      }
    }
  ],
  "output_format": "mp4"
}
```

#### 5. Download Video
```
GET /api/v1/download/{video_id}
```
Download processed video.

#### 6. Get Features
```
GET /api/v1/features
```
Get list of available features.

## Using Docker

### Build and Run
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Logs
```bash
docker-compose logs -f api
```

## Project Structure
```
filmy-ai/
├── app/
│   ├── api/              # API routes
│   ├── models/           # Pydantic schemas
│   ├── services/         # Business logic
│   ├── utils/            # Utilities
│   └── config.py         # Configuration
├── tests/                # Unit tests
├── data/                 # Data directory
│   ├── temp_videos/      # Uploaded videos
│   └── output_videos/    # Processed videos
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
└── docker-compose.yml  # Docker compose configuration
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
# Install dev dependencies
pip install black flake8

# Format code
black app/

# Check linting
flake8 app/
```

## Next Steps

1. **Implement AI Models**: Replace placeholder logic in `VideoService` with actual AI models
2. **Add Database**: Configure PostgreSQL or MongoDB for metadata storage
3. **Implement Async Tasks**: Use Celery for long-running video processing
4. **Add Authentication**: Implement API key authentication
5. **Deploy**: Use cloud services (AWS, GCP, Azure) for production deployment

## Common Issues

### Port Already in Use
```bash
# Change port in .env or command line
python main.py --port 8001
```

### FFmpeg Not Found
Ensure FFmpeg is installed and in system PATH:
```bash
ffmpeg -version
```

### Out of Memory
Reduce `MAX_VIDEO_SIZE_MB` in .env for large videos.

## Support
For issues and feature requests, check the project repository or contact the development team.
