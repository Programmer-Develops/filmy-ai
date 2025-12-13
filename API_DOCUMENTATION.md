# Filmy AI API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Currently using API Key (to be implemented):
```
Authorization: Bearer YOUR_API_KEY
```

## Response Format
All responses follow standard format:

### Success Response
```json
{
  "status": "success",
  "message": "Operation completed",
  "data": {}
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description",
  "detail": "Detailed error message"
}
```

## Endpoints

### 1. Health Check
**Endpoint:** `GET /health`

**Description:** Check API health status

**Response:**
```json
{
  "status": "healthy",
  "service": "Filmy AI API",
  "version": "0.1.0"
}
```

---

### 2. Upload Video
**Endpoint:** `POST /upload/video`

**Description:** Upload a video file for processing

**Request:**
- Content-Type: `multipart/form-data`
- Parameter: `file` (binary)

**Supported Formats:**
- MP4
- AVI
- MOV
- MKV
- FLV

**Max File Size:** 500 MB (configurable)

**Response:**
```json
{
  "status": "success",
  "video_id": "20231213_120000_video.mp4",
  "message": "Video uploaded successfully: video.mp4",
  "size_mb": 150.5
}
```

**Error Responses:**
```json
{
  "status": "error",
  "detail": "File type video/webm not allowed. Supported: ['video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo']"
}
```

---

### 3. Get Features
**Endpoint:** `GET /features`

**Description:** Get list of available enhancement and editing features

**Response:**
```json
{
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
  "supported_formats": ["mp4", "avi", "mov", "mkv", "flv"]
}
```

---

### 4. Enhance Video
**Endpoint:** `POST /enhance/video`

**Description:** Apply AI-powered enhancement to a video

**Request:**
```json
{
  "video_id": "20231213_120000_video.mp4",
  "enhancement_type": "upscale",
  "settings": {
    "intensity": 0.8,
    "preserve_quality": true,
    "custom_params": {}
  }
}
```

**Parameters:**
- `video_id` (string, required): ID of uploaded video
- `enhancement_type` (string, required): Type of enhancement
  - `upscale` - 2x to 4x upscaling
  - `denoise` - Noise reduction
  - `color_correction` - Auto color balance
  - `stabilization` - Video stabilization
  - `super_resolution` - Advanced upscaling
  - `motion_blur_removal` - Motion blur reduction
- `settings` (object, optional):
  - `intensity` (float, 0-1): Enhancement strength
  - `preserve_quality` (boolean): Keep original quality aspects
  - `custom_params` (object): Model-specific parameters

**Response:**
```json
{
  "status": "success",
  "message": "Video enhanced with upscale",
  "output_path": "/data/output_videos/upscale_20231213_120000_video.mp4",
  "processing_time": 45.23
}
```

---

### 5. Edit Video
**Endpoint:** `POST /edit/video`

**Description:** Apply editing operations to a video

**Request:**
```json
{
  "video_id": "20231213_120000_video.mp4",
  "operations": [
    {
      "operation_type": "trim",
      "start_time": 5.0,
      "end_time": 120.0,
      "parameters": {}
    },
    {
      "operation_type": "crop",
      "parameters": {
        "x": 0,
        "y": 0,
        "width": 1280,
        "height": 720
      }
    },
    {
      "operation_type": "rotate",
      "parameters": {
        "angle": 90
      }
    },
    {
      "operation_type": "resize",
      "parameters": {
        "width": 1920,
        "height": 1080
      }
    }
  ],
  "output_format": "mp4"
}
```

**Operations:**

1. **Trim**
   - Parameters: `start_time`, `end_time` (seconds)
   
2. **Crop**
   - Parameters: `x`, `y`, `width`, `height`
   
3. **Rotate**
   - Parameters: `angle` (0, 90, 180, 270)
   
4. **Resize**
   - Parameters: `width`, `height` (pixels)
   
5. **Speed Adjust**
   - Parameters: `speed` (0.5-2.0)
   
6. **Brightness/Contrast**
   - Parameters: `brightness` (-1.0 to 1.0), `contrast` (-1.0 to 1.0)

**Response:**
```json
{
  "status": "success",
  "message": "Video edited successfully",
  "output_path": "/data/output_videos/edited_20231213_120000_video.mp4",
  "processing_time": 120.45
}
```

---

### 6. Get Video Status
**Endpoint:** `GET /status/{video_id}`

**Description:** Get processing status of a video

**Response:**
```json
{
  "video_id": "20231213_120000_video.mp4",
  "status": "completed"
}
```

**Status Values:**
- `processing` - Currently being processed
- `completed` - Processing finished
- `failed` - Processing failed
- `queued` - Waiting in queue

---

### 7. Download Video
**Endpoint:** `GET /download/{video_id}`

**Description:** Download processed video

**Parameters:**
- `video_id` (path, required): ID of output video

**Response:** Binary video file

**Headers:**
- `Content-Type: video/mp4`
- `Content-Disposition: attachment`

---

## Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid request parameters |
| 404 | Not Found | Video not found |
| 413 | Payload Too Large | File exceeds size limit |
| 415 | Unsupported Media Type | File type not supported |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

---

## Rate Limiting
Coming soon. Currently no rate limits.

---

## Example Usage

### cURL
```bash
# Upload video
curl -X POST "http://localhost:8000/api/v1/upload/video" \
  -F "file=@video.mp4"

# Enhance video
curl -X POST "http://localhost:8000/api/v1/enhance/video" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "20231213_120000_video.mp4",
    "enhancement_type": "upscale",
    "settings": {"intensity": 0.8}
  }'

# Download result
curl -X GET "http://localhost:8000/api/v1/download/upscale_20231213_120000_video.mp4" \
  -o output.mp4
```

### Python
```python
import requests

# Upload
files = {'file': open('video.mp4', 'rb')}
response = requests.post('http://localhost:8000/api/v1/upload/video', files=files)
video_id = response.json()['video_id']

# Enhance
payload = {
    'video_id': video_id,
    'enhancement_type': 'upscale',
    'settings': {'intensity': 0.8}
}
response = requests.post('http://localhost:8000/api/v1/enhance/video', json=payload)

# Download
response = requests.get(f'http://localhost:8000/api/v1/download/{video_id}')
with open('output.mp4', 'wb') as f:
    f.write(response.content)
```

### JavaScript/Fetch
```javascript
// Upload
const formData = new FormData();
formData.append('file', fileInput.files[0]);
const uploadResponse = await fetch('http://localhost:8000/api/v1/upload/video', {
  method: 'POST',
  body: formData
});
const { video_id } = await uploadResponse.json();

// Enhance
const enhanceResponse = await fetch('http://localhost:8000/api/v1/enhance/video', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    video_id,
    enhancement_type: 'upscale',
    settings: { intensity: 0.8 }
  })
});
```

---

## Versioning
Current API version: **v1**

Future versions will maintain backward compatibility or provide migration guides.
