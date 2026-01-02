# 🎬 Filmy-AI: An AI Agent for Video Editing

[![GitHub stars](https://img.shields.io/github/stars/yourusername/filmy-ai?style=social)](https://github.com/yourusername/filmy-ai)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/filmy-ai?style=social)](https://github.com/yourusername/filmy-ai)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green)](https://fastapi.tiangolo.com/)

> **Automate your video editing workflow with the power of Generative AI and Python.**

**⭐ If you find this project useful, please give it a star! It helps more people discover Filmy-AI and motivates further development.**

---

## 🌐 Live API

**Try Filmy-AI right now**:
- 🚀 **Hosted API**: https://shantanu-pandya-filmy-ai-api.hf.space/
---

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [How to Use](#how-to-use)
- [Web Integration Guide](#web-integration-guide)
- [API Documentation](#api-documentation)
- [License & Attribution](#license--attribution)
- [Contributing](#contributing)

---

## 🎯 Overview

**Filmy-AI** is an intelligent video editing agent powered by Google's Gemini AI and MoviePy. It allows users to describe video edits in natural language, and the AI automatically processes and applies those edits to their videos.

Instead of manually editing videos frame-by-frame, just tell the AI what you want:
- *"Remove background noise and add background music"*
- *"Cut the first 5 seconds and make it black & white"*
- *"Add subtitles and blur faces"*

The AI understands your instructions and applies them automatically!

### ✨ Key Features

- 🤖 **Natural Language Processing**: Describe edits in plain English
- 🎥 **Multi-format Support**: MP4, AVI, MOV, MKV, FLV
- ⚡ **Fast Processing**: GPU-accelerated video encoding
- 🔌 **REST API**: Easy integration with websites and applications
- 💾 **Scalable**: Redis-based task queue with Celery workers
- 🐳 **Docker Ready**: One-click deployment

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose (optional, for containerized deployment)
- Google Gemini API key ([Get one here](https://ai.google.dev))

### Local Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/filmy-ai.git
cd filmy-ai
```

2. **Create a virtual environment**
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
Create a `.env` file in the root directory:
```env
API_PORT=8000
API_HOST=0.0.0.0
DEBUG=False
ENVIRONMENT=production
GEMINI_API_KEY=your-gemini-api-key-here
DATABASE_URL=sqlite:///./data/filmy_ai.db
REDIS_URL=redis://localhost:6379/0
```

5. **Run the server**
```bash
python main.py
```

The API will be available at `http://localhost:8000`

---

## 📖 How to Use

### **REST API** (For Developers & Integration)

**Base URL:**
- 🌐 **Production (Hosted)**: `https://shantanu-pandya-filmy-ai-api.hf.space/api/v1`
- 💻 **Local**: `http://localhost:8000/api/v1`

#### Step 1: Upload a Video
```bash
curl -X POST "https://shantanu-pandya-filmy-ai-api.hf.space/api/v1/upload/video" \
  -F "file=@myvideo.mp4"
```

**Response:**
```json
{
  "status": "success",
  "video_id": "video_12345.mp4",
  "filename": "video_12345.mp4",
  "message": "Video uploaded successfully: myvideo.mp4"
}
```

#### Step 2: Send AI Instructions
```bash
curl -X POST "https://shantanu-pandya-filmy-ai-api.hf.space/api/v1/instruct" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "video_12345.mp4",
    "instruction": "Remove background noise and make it 720p"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Video processed successfully",
  "output_file": "video_12345_edited.mp4",
  "processing_time_seconds": 45.23
}
```

#### Step 3: Download the Processed Video
```bash
curl "https://shantanu-pandya-filmy-ai-api.hf.space/api/v1/download/video_12345_edited.mp4" \
  -o edited_video.mp4
```

---

## 🌐 Web Integration Guide

### Integration for Website Owners

If you want to add Filmy-AI to your website, integrate with the live API:

#### Option 1: Custom Frontend Integration

Create your own frontend using JavaScript:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Video Editor on My Website</title>
</head>
<body>
    <input type="file" id="videoInput" accept="video/*" />
    <button onclick="uploadVideo()">Upload</button>
    
    <textarea id="instructions" placeholder="Describe edits here..."></textarea>
    <button onclick="processVideo()">Process with AI</button>
    
    <div id="status"></div>
    <video id="preview" controls></video>

    <script>
        const API_URL = 'https://shantanu-pandya-filmy-ai-api.hf.space/api/v1';
        let videoId = null;

        async function uploadVideo() {
            const file = document.getElementById('videoInput').files[0];
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch(`${API_URL}/upload/video`, {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                videoId = data.video_id;
                document.getElementById('status').innerText = '✅ Video uploaded!';
            } catch (error) {
                document.getElementById('status').innerText = '❌ Upload failed: ' + error.message;
            }
        }

        async function processVideo() {
            const instructions = document.getElementById('instructions').value;
            
            try {
                const response = await fetch(`${API_URL}/instruct`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        video_id: videoId,
                        instruction: instructions
                    })
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    document.getElementById('status').innerText = '✅ Done! Downloading...';
                    document.getElementById('preview').src = `${API_URL}/download/${data.output_file}`;
                } else {
                    throw new Error(data.message);
                }
            } catch (error) {
                document.getElementById('status').innerText = '❌ Processing failed: ' + error.message;
            }
        }
    </script>
</body>
</html>
```

#### Option 2: React/Vue Component

```javascript
// React Example
import React, { useState } from 'react';

export default function VideoEditor() {
    const [videoId, setVideoId] = useState(null);
    const [status, setStatus] = useState('');
    const API_URL = 'https://shantanu-pandya-filmy-ai-api.hf.space/api/v1';

    const uploadVideo = async (e) => {
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch(`${API_URL}/upload/video`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            setVideoId(data.video_id);
            setStatus('✅ Video uploaded!');
        } catch (err) {
            setStatus('❌ Upload failed: ' + err.message);
        }
    };

    return (
        <div>
            <input type="file" accept="video/*" onChange={uploadVideo} />
            <p>{status}</p>
        </div>
    );
}
```

---

## 📚 API Documentation

For detailed API endpoint documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

### Available Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/upload/video` | POST | Upload video file |
| `/instruct` | POST | Process with AI instructions (blocks until complete) |
| `/download/{filename}` | GET | Download processed video |

---

## � Security Notes

- 🔑 **Never commit API keys**: Use environment variables
- 📝 **Add authentication**: Implement API key auth for production
- 💾 **Validate uploads**: Check file size and type before processing

---

## 📝 Example Use Cases

- 📺 **Content Creators**: Batch process YouTube videos
- 🎓 **Educators**: Create edited educational content
- 🎥 **Social Media**: Generate TikTok/Instagram video edits
- 🎬 **Video Production**: Automate editing workflows
- 🤖 **Video APIs**: Integrate into SaaS platforms

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## ⭐ Support

If you find Filmy-AI useful, please consider:
- ⭐ Giving it a star on GitHub
- 🐛 Reporting bugs and suggesting features
- 📢 Sharing it with others
- 🤝 Contributing to the project

---

## 📄 License & Attribution

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) for details.

### ⚠️ Important: Attribution Required

If you use, fork, or build upon Filmy-AI, **you MUST include proper attribution**:

**In your README or documentation, include:**
```markdown
This project uses [Filmy-AI](https://github.com/yourusername/filmy-ai) 
- An AI-powered video editing API by [Shantanu Pandya](https://github.com/yourusername)
```

**For commercial projects:**
- Include the above attribution in your project documentation
- Include LICENSE notice in your codebase
- Link back to the original repository

**Copying code without attribution is not permitted and violates the MIT License terms.**

### License Summary
- ✅ **Allowed**: Use, modify, distribute (with attribution)
- ✅ **Required**: Include original license and author credit
- ✅ **Allowed**: Use in commercial projects
- ❌ **Not Allowed**: Remove original license or author credits
- ❌ **Not Allowed**: Claim code as your own without attribution

---

**Made with ❤️ by [Shantanu Pandya](https://github.com/Programmer-Develops)**

*If you use this project, please give credit where it's due!* 🙏

---

## ⭐ Show Your Support

Every star means a lot! If Filmy-AI helped you:
- ⭐ **Star this repo** - Biggest motivation!
- 🍴 **Fork it** - Build awesome things with it
- 🐛 **Report issues** - Help improve the project
- 📢 **Share it** - Spread the word (with credit!)
- 🤝 **Contribute** - Submit PRs