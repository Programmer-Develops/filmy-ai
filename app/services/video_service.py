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
    from moviepy.editor import VideoFileClip, AudioArrayClip, TextClip, CompositeVideoClip, ImageClip
    import moviepy.video.fx.all as vfx
    logger_name = "MoviePy v1"
except ImportError:
    # Try MoviePy v2.x layout
    from moviepy import VideoFileClip, AudioArrayClip, TextClip, CompositeVideoClip, ImageClip
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
        - "texts": (array) list of objects: {"text": str, "start": float, "end": float, "position": str, "fontsize": int, "color": str}
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
        """Remove audio noise with reduced memory footprint using streaming/chunking"""
        try:
            if not audio_clip: return None
            rate = int(getattr(audio_clip, "fps", 44100))
            settings = get_settings()
            chunk_duration = settings.audio_chunk_duration  # Configurable chunk size
            
            duration = audio_clip.duration
            num_chunks = int(np.ceil(duration / chunk_duration))
            
            cleaned_chunks = []
            
            for i in range(num_chunks):
                start_time = i * chunk_duration
                end_time = min((i + 1) * chunk_duration, duration)
                
                # Extract only this chunk
                chunk_clip = audio_clip.subclipped(start_time, end_time) if hasattr(audio_clip, 'subclipped') else audio_clip.subclip(start_time, end_time)
                audio_array = chunk_clip.to_soundarray(fps=rate)
                
                # Reduce noise on chunk
                if audio_array.ndim > 1:
                    data = audio_array.T 
                    reduced = nr.reduce_noise(y=data, sr=rate, stationary=True)
                    clean = reduced.T 
                else:
                    clean = nr.reduce_noise(y=audio_array, sr=rate, stationary=True)
                
                cleaned_chunks.append(clean)
                
                # Free memory after processing chunk
                del audio_array, chunk_clip
            
            # Concatenate cleaned chunks
            full_clean = np.concatenate(cleaned_chunks, axis=0)
            return AudioArrayClip(full_clean, fps=rate)
        except Exception as e:
            logger.error(f"Noise reduction error: {e}")
            return audio_clip

    def _apply_texts_to_clip(self, clip, texts):
        if not texts:
            return clip

        text_clips = []
        duration = clip.duration

        for t in texts:
            try:
                content = str(t.get("text", ""))
                if not content: continue

                start = float(t.get("start", 0))
                end = t.get("end")
                end = float(end) if end is not None else duration
                dur = max(0.01, min(end, duration) - start)

                fontsize = int(t.get("fontsize", 40))
                color = t.get("color", "white")
                font_path = t.get("font")
                position = t.get("position", "center")

                # 1. Try TextClip (Requires ImageMagick)
                try:
                    txt_clip = TextClip(content, fontsize=fontsize, color=color, font=font_path) if font_path else TextClip(content, fontsize=fontsize, color=color)
                    txt_clip = txt_clip.set_duration(dur).set_start(start).set_pos(position)
                    text_clips.append(txt_clip)
                
                # 2. PIL Fallback (Modern Pillow 10+ compatible)
                except Exception:
                    from PIL import Image, ImageDraw, ImageFont
                    
                    try:
                        font_obj = ImageFont.truetype(font_path, fontsize) if font_path else ImageFont.load_default()
                    except:
                        font_obj = ImageFont.load_default()

                    # Use getbbox() instead of deprecated textsize()
                    left, top, right, bottom = font_obj.getbbox(content)
                    tw, th = right - left, bottom - top

                    # Create canvas with padding
                    img = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(img)
                    # Draw text offset by the bounding box start to prevent clipping
                    draw.text((10 - left, 10 - top), content, font=font_obj, fill=color)

                    img_clip = ImageClip(np.array(img))
                    
                    # Set duration and start - handle both MoviePy v1 and v2
                    if hasattr(img_clip, 'set_duration'):
                        img_clip = img_clip.set_duration(dur).set_start(start)
                    elif hasattr(img_clip, 'with_duration'):
                        img_clip = img_clip.with_duration(dur).with_start(start)
                    else:
                        img_clip.duration = dur
                        img_clip.start = start
                    
                    # Manual Position Handling for ImageClip
                    # Ensuring `pos` is a callable that returns numeric (x, y) coordinates
                    def _safe_size(c, default=0):
                        try:
                            return getattr(c, 'w', None) or (c.size[0] if hasattr(c, 'size') else default)
                        except Exception:
                            return default

                    iw = _safe_size(img_clip, 0)
                    ih = _safe_size(img_clip, 0)

                    if position == "center":
                        pos = lambda t: ((clip.w - iw) / 2, (clip.h - ih) / 2)
                    elif position == "top-left":
                        pos = lambda t: (20, 20)
                    elif position == "top-right":
                        pos = lambda t: (max(0, clip.w - iw - 20), 20)
                    elif position == "bottom-left":
                        pos = lambda t: (20, max(0, clip.h - ih - 20))
                    elif position == "bottom-right":
                        pos = lambda t: (max(0, clip.w - iw - 20), max(0, clip.h - ih - 20))
                    else:
                        # default to center
                        pos = lambda t: ((clip.w - iw) / 2, (clip.h - ih) / 2)

                    # Prefer the native setter when available (it accepts strings or callables).
                    if hasattr(img_clip, 'set_pos'):
                        img_clip = img_clip.set_pos(pos)
                    else:
                        # assign a callable that returns numeric tuple to avoid MoviePy attempting to call strings
                        img_clip.pos = pos
                    
                    text_clips.append(img_clip)

            except Exception as e:
                logger.warning(f"Failed overlay for '{content}': {e}")

        if not text_clips: return clip
        
        # Composite layers
        result = CompositeVideoClip([clip] + text_clips)
        
        # Set duration - handle both MoviePy v1 and v2
        if hasattr(result, 'set_duration'):
            return result.set_duration(clip.duration)
        elif hasattr(result, 'with_duration'):
            return result.with_duration(clip.duration)
        else:
            result.duration = clip.duration
            return result

    async def edit_video_by_instruction(self, video_path: str, instruction: str) -> Dict[str, Any]:
        video_id = os.path.basename(video_path)
        self.processing_status[video_id] = "processing"
        
        commands = await self._get_ai_instructions(instruction)
        
        try:
            clip = VideoFileClip(video_path)
            
            # --- TRIMMING ---
            if commands.get("trim_start") or commands.get("trim_end"):
                try:
                    s = float(commands.get("trim_start", 0))
                    e = clip.duration - float(commands.get("trim_end", 0))
                    clip = clip.subclipped(s, e) if hasattr(clip, "subclipped") else clip.subclip(s, e)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid trim values: start={commands.get('trim_start')}, end={commands.get('trim_end')}")

            # --- AUDIO ---
            if commands.get("remove_noise") and clip.audio:
                clip.audio = self._remove_audio_noise(clip.audio)

            if commands.get("volume_boost", 1.0) != 1.0:
                try:
                    boost = float(commands.get("volume_boost", 1.0))
                    if boost != 1.0 and clip.audio:
                        if hasattr(clip.audio, "multiply_volume"):
                            clip.audio = clip.audio.multiply_volume(boost)
                        else:
                            clip.audio = clip.audio.volumex(boost)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid volume_boost value: {commands.get('volume_boost')}")

            # --- VISUALS ---
            if commands.get("grayscale"):
                if vfx and hasattr(vfx, 'blackwhite'):
                    clip = clip.fx(vfx.blackwhite)
                else:
                    clip = clip.image_transform(lambda im: np.dstack([np.dot(im[...,:3], [0.299, 0.587, 0.114])] * 3).astype('uint8'))
            
            if commands.get("speed", 1.0) != 1.0:
                try:
                    speed_val = float(commands.get("speed", 1.0))
                    if speed_val != 1.0 and vfx and hasattr(vfx, 'speedx'):
                        clip = clip.fx(vfx.speedx, speed_val)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid speed value: {commands.get('speed')}")

            # --- TEXT OVERLAYS ---
            if commands.get("texts"):
                clip = self._apply_texts_to_clip(clip, commands.get("texts"))

            # --- OUTPUT ---
            output_dir = os.path.dirname(video_path).replace("temp_videos", "output_videos")
            os.makedirs(output_dir, exist_ok=True)
            output_filename = f"edited_{int(datetime.now().timestamp())}_{video_id}.mp4"
            output_path = os.path.join(output_dir, output_filename)

            # Optimize for low RAM usage: use lower bitrate, preset, and ffmpeg parameters
            settings = get_settings()
            clip.write_videofile(
                output_path, 
                codec="libx264",
                audio_codec="aac",
                preset=settings.video_preset,  # faster encoding, less RAM
                bitrate=settings.video_bitrate,  # Reduce bitrate to lower RAM usage
                ffmpeg_params=["-crf", str(settings.video_crf)]  # Quality setting
            )
            
            clip.close()
            self.processing_status[video_id] = "completed"
            return {"status": "success", "output_path": output_path, "operations": commands}

        except Exception as e:
            logger.exception("Editing Failed")
            return {"status": "error", "message": str(e)}

    async def get_status(self, video_id: str) -> str:
        return self.processing_status.get(video_id, "unknown")