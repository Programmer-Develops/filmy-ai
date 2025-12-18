import os
import json
import logging
import re
import numpy as np
import noisereduce as nr
import google.generativeai as genai
from typing import Dict, Any
from fastapi import UploadFile
from datetime import datetime

# --- UNIVERSAL MOVIEPY LOADER ---
try:
    # Try MoviePy v1.x layout
    from moviepy.editor import VideoFileClip, AudioArrayClip
    import moviepy.video.fx.all as vfx
    logger_name = "MoviePy v1"
except ImportError:
    # Try MoviePy v2.x layout
    from moviepy import VideoFileClip, AudioArrayClip
    import moviepy.video.fx as vfx
    logger_name = "MoviePy v2"

from app.config import get_settings

logger = logging.getLogger(__name__)

class VideoService:
    def __init__(self):
        self.processing_status = {}
        settings = get_settings()
        gemini_api_key = settings.gemini_api_key
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not configured.")
        
        genai.configure(api_key=gemini_api_key)
        # Note: Ensure your model name is correct (e.g., 'gemini-1.5-flash')
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def save_upload(self, file: UploadFile, temp_dir: str) -> str:
        os.makedirs(temp_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = file.filename.replace(" ", "_")
        file_path = os.path.join(temp_dir, f"{timestamp}_{safe_filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Video saved: {file_path}")
        return file_path   

    async def _get_ai_instructions(self, user_prompt: str) -> Dict:
        system_prompt = """
        Map the user's request to a JSON object:
        - "trim_start": (float) seconds to cut from start.
        - "trim_end": (float) seconds to cut from end.
        - "remove_noise": (boolean)
        - "speed": (float) 1.0 is normal.
        - "volume_boost": (float) 1.0 is normal.
        - "grayscale": (boolean)
        Return ONLY JSON.
        """
        try:
            response = self.model.generate_content(f"{system_prompt}\nUser Request: {user_prompt}")
            text = response.text.strip()
            if "```" in text:
                text = text.replace("```json", "").replace("```", "")
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini parsing failed: {e}")
            return {}

    def _remove_audio_noise(self, audio_clip):
        try:
            if not audio_clip: return None
            rate = int(getattr(audio_clip, "fps", 44100))
            audio_array = audio_clip.to_soundarray(fps=rate)
            
            if audio_array.ndim > 1:
                data = audio_array.T 
                reduced = nr.reduce_noise(y=data, sr=rate, stationary=True)
                clean = reduced.T 
            else:
                clean = nr.reduce_noise(y=audio_array, sr=rate, stationary=True)
            
            return AudioArrayClip(clean, fps=rate)
        except Exception as e:
            logger.error(f"Noise reduction error: {e}")
            return audio_clip

    async def edit_video_by_instruction(self, video_path: str, instruction: str) -> Dict[str, Any]:
        video_id = os.path.basename(video_path)
        self.processing_status[video_id] = "processing"
        
        commands = await self._get_ai_instructions(instruction)
        
        try:
            clip = VideoFileClip(video_path)
            
            # --- VERSION AGNOSTIC TRIMMING ---
            if commands.get("trim_start") or commands.get("trim_end"):
                s = float(commands.get("trim_start", 0))
                e = clip.duration - float(commands.get("trim_end", 0))
                
                if hasattr(clip, "subclipped"): # MoviePy v2.x
                    clip = clip.subclipped(s, e)
                else: # MoviePy v1.x
                    clip = clip.subclip(s, e)

            # --- AUDIO NOISE ---
            if commands.get("remove_noise"):
                if clip.audio:
                    clip.audio = self._remove_audio_noise(clip.audio)

            # --- COLOR EFFECTS ---
            if commands.get("grayscale"):
                if vfx and hasattr(vfx, 'blackwhite'):
                    clip = clip.fx(vfx.blackwhite)
                elif vfx and hasattr(vfx, 'black_white'):
                    clip = clip.fx(vfx.black_white)
                else:
                    # Manual fallback if vfx fails
                    clip = clip.image_transform(lambda im: np.dstack([np.dot(im[...,:3], [0.299, 0.587, 0.114])] * 3).astype('uint8'))
            
            # --- SPEED ---
            if commands.get("speed", 1.0) != 1.0:
                speed_val = float(commands["speed"])
                if vfx and hasattr(vfx, 'speedx'):
                    clip = clip.fx(vfx.speedx, speed_val)
                
            # --- VOLUME ---
            if commands.get("volume_boost", 1.0) != 1.0:
                boost = float(commands["volume_boost"])
                if clip.audio:
                    try:
                        # Method 1: MoviePy v2.x (Newest)
                        if hasattr(clip.audio, "multiply_volume"):
                            clip.audio = clip.audio.multiply_volume(boost)
                        # Method 2: MoviePy v1.x (Legacy)
                        elif hasattr(clip.audio, "volumex"):
                            clip.audio = clip.audio.volumex(boost)
                        # Method 3: Direct Multiplication (Universal fallback)
                        else:
                            clip.audio = clip.audio.with_effects([lambda a: a * boost])
                    except Exception as vol_err:
                        logger.warning(f"Could not apply volume boost: {vol_err}")

            # --- OUTPUT ---
            output_dir = os.path.dirname(video_path).replace("temp_videos", "output_videos")
            os.makedirs(output_dir, exist_ok=True)
            
            output_filename = f"edited_{int(datetime.now().timestamp())}_{video_id}"
            output_path = os.path.join(output_dir, output_filename)

            clip.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac", 
                preset="ultrafast",
                logger=None
            )
            
            clip.close()
            self.processing_status[video_id] = "completed"
            
            return {
                "status": "success",
                "output_path": output_path,
                "operations": commands
            }

        except Exception as e:
            logger.error(f"Editing Failed: {e}")
            return {"status": "error", "message": str(e)}

    async def get_status(self, video_id: str) -> str:
        return self.processing_status.get(video_id, "unknown")