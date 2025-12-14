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
from moviepy import VideoFileClip, AudioArrayClip
import moviepy.video.fx as vfx
logger = logging.getLogger(__name__)

# --- ROBUST IMPORT SECTION ---
# 1. Import Core Classes
# try:
#     # MoviePy v2.x
#     from moviepy import VideoFileClip, AudioArrayClip
#     logger.info("Imported VideoFileClip from moviepy (v2)")
# except ImportError:
#     # MoviePy v1.x
#     from moviepy.editor import VideoFileClip, AudioArrayClip
#     logger.info("Imported VideoFileClip from moviepy.editor (v1)")

# # 2. Import Effects (Separately to prevent crash)
# vfx = None
# try:
#     # Try v1 style first as it's often aliased
#     import moviepy.video.fx.all as vfx
# except ImportError:
#     try:
#         # Try v2 style
#         import moviepy.video.fx as vfx
#     except ImportError:
#         logger.warning("Could not import moviepy.video.fx. Visual effects might fail.")

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class VideoService:
    def __init__(self):
        self.processing_status = {}
        # Using flash model for speed
        self.model = genai.GenerativeModel('gemini-1.5-flash')

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
        """
        Uses Gemini to translate natural language into editing commands.
        """
        system_prompt = """
        You are a video editing API. 
        Map the user's request to a JSON object with these keys:
        - "trim_start": (float) seconds to cut from start.
        - "trim_end": (float) seconds to cut from end.
        - "remove_noise": (boolean) true if user mentions noise/audio cleaning.
        - "speed": (float) 1.0 is normal. >1 is fast.
        - "volume_boost": (float) 1.0 is normal.
        - "grayscale": (boolean) true if user wants black and white/B&W.

        Return ONLY the JSON. Example: {"grayscale": true, "remove_noise": true}
        """
        
        try:
            response = self.model.generate_content(f"{system_prompt}\nUser Request: {user_prompt}")
            text = response.text.strip()
            
            # Clean up code blocks if Gemini adds them
            if "```" in text:
                text = text.replace("```json", "").replace("```", "")
            
            # Use regex to find the JSON part if there is extra text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)

            data = json.loads(text)
            logger.info(f"AI Parsed Instructions: {data}")
            return data
        except Exception as e:
            logger.error(f"Gemini parsing failed: {e}. Raw text: {response.text if 'response' in locals() else 'N/A'}")
            
            # FALLBACK: Force specific edits if AI parsing failed but keywords exist
            fallback = {}
            p = user_prompt.lower()
            if "black" in p and "white" in p: fallback["grayscale"] = True
            if "noise" in p or "clean" in p: fallback["remove_noise"] = True
            if "fast" in p: fallback["speed"] = 1.5
            if "loud" in p: fallback["volume_boost"] = 1.5
            
            if fallback:
                logger.info(f"Using fallback keywords: {fallback}")
                return fallback
                
            return {}

    def _remove_audio_noise(self, audio_clip):
        try:
            if not audio_clip: return None
            
            # MoviePy v2 compatibility: fps might be an attribute or method arg
            rate = 44100
            if hasattr(audio_clip, "fps") and audio_clip.fps:
                 rate = int(audio_clip.fps)

            # Get audio data
            # In v2, to_soundarray typically works
            audio_array = audio_clip.to_soundarray(fps=rate)
            
            # Noisereduce expects shape (samples,) or (channels, samples)
            # MoviePy gives (samples, channels)
            if audio_array.ndim > 1:
                data = audio_array.T # Transpose to (channels, samples)
                reduced = nr.reduce_noise(y=data, sr=rate, stationary=True)
                clean = reduced.T # Transpose back
            else:
                clean = nr.reduce_noise(y=audio_array, sr=rate, stationary=True)
            
            return AudioArrayClip(clean, fps=rate)
        except Exception as e:
            logger.error(f"Noise reduction error: {e}")
            return audio_clip

    async def edit_video_by_instruction(self, video_path: str, instruction: str) -> Dict[str, Any]:
        video_id = os.path.basename(video_path)
        self.processing_status[video_id] = "processing"
        
        # 1. Get Instructions
        commands = await self._get_ai_instructions(instruction)
        
        if not commands:
            logger.warning("No editing commands generated! Video will remain unchanged.")

        try:
            # 2. Load Video
            clip = VideoFileClip(video_path)
            
            # 3. Apply Edits
            if commands.get("trim_start") or commands.get("trim_end"):
                s = commands.get("trim_start", 0)
                e = clip.duration - commands.get("trim_end", 0)
                clip = clip.subclip(s, e)

            if commands.get("remove_noise"):
                logger.info("Applying noise reduction")
                if clip.audio:
                    clip.audio = self._remove_audio_noise(clip.audio)

            if commands.get("grayscale"):
                logger.info("Applying grayscale")
                # Safely attempt Black & White effect
                if vfx and hasattr(vfx, 'blackwhite'):
                    clip = clip.fx(vfx.blackwhite)
                elif vfx and hasattr(vfx, 'black_white'):
                     clip = clip.fx(vfx.black_white)
                else:
                    # Manual Grayscale if fx is missing (common in v2 betas)
                    # This converts RGB to Grayscale manually
                    clip = clip.image_transform(lambda im: np.dstack([np.dot(im[...,:3], [0.299, 0.587, 0.114])] * 3).astype('uint8'))
            
            if commands.get("speed", 1.0) != 1.0:
                if vfx and hasattr(vfx, 'speedx'):
                    clip = clip.fx(vfx.speedx, commands["speed"])
                
            if commands.get("volume_boost", 1.0) != 1.0:
                if clip.audio:
                    arr = clip.audio.to_soundarray()
                    new_arr = arr * commands["volume_boost"]
                    clip.audio = AudioArrayClip(new_arr, fps=clip.audio.fps)

            # 4. Save Output
            output_dir = os.path.dirname(video_path).replace("temp_videos", "output_videos")
            os.makedirs(output_dir, exist_ok=True)
            
            output_filename = f"edited_{int(datetime.now().timestamp())}_{video_id}"
            output_path = os.path.join(output_dir, output_filename)

            # Use ultrafast preset for quick feedback
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
                "operations": commands,
                "message": "Edited successfully"
            }

        except Exception as e:
            logger.error(f"Editing Failed: {e}")
            return {"status": "error", "message": str(e)}

    # Compatibility wrapper
    async def enhance_video(self, video_path: str, enhancement_type: str, settings: Dict) -> Dict:
        return await self.edit_video_by_instruction(video_path, f"Perform {enhancement_type}")

    async def get_status(self, video_id: str) -> str:
        return self.processing_status.get(video_id, "unknown")