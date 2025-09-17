# models/video_processor.py
"""
Complete Whisper integration for video transcription
"""
from transformers import pipeline
import torch
from moviepy.editor import VideoFileClip
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, model_size="base"):
        """
        Initialize video processor with Whisper
        model_size options: tiny, base, small, medium, large
        """
        self.model_size = model_size
        self.model_name = f"openai/whisper-{model_size}"
        
        # Check for GPU availability
        self.device = 0 if torch.cuda.is_available() else -1
        
        try:
            # Initialize Whisper pipeline
            self.transcriber = pipeline(
                "automatic-speech-recognition",
                model=self.model_name,
                device=self.device,
                return_timestamps=False  # Set to True if you want timestamps
            )
            logger.info(f"✅ Loaded Whisper model: {self.model_name} on {'GPU' if self.device >= 0 else 'CPU'}")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {str(e)}")
            raise Exception(f"Could not initialize Whisper: {str(e)}")
    
    def extract_audio_from_video(self, video_path):
        """Extract audio from video file using MoviePy"""
        try:
            logger.info(f"🎬 Extracting audio from: {video_path}")
            
            # Load video
            video = VideoFileClip(video_path)
            
            # Check if video has audio
            if video.audio is None:
                video.close()
                return None, "Video file contains no audio track"
            
            # Create temporary audio file
            audio_path = tempfile.mktemp(suffix='.wav')
            
            # Extract audio to WAV format (best for Whisper)
            video.audio.write_audiofile(
                audio_path,
                logger=None,  # Suppress MoviePy logs
                verbose=False
            )
            
            # Clean up video object
            video.close()
            
            logger.info(f"✅ Audio extracted successfully to: {audio_path}")
            return audio_path, None
            
        except Exception as e:
            logger.error(f"❌ Error extracting audio: {str(e)}")
            return None, f"Failed to extract audio: {str(e)}"
    
    def transcribe_audio(self, audio_path):
        """Transcribe audio using Whisper"""
        try:
            logger.info(f"🎤 Transcribing audio with Whisper {self.model_size}")
            
            # Transcribe with Whisper
            result = self.transcriber(audio_path)
            
            # Extract text from result
            transcript = result.get("text", "").strip()
            
            if not transcript:
                return None, "No speech detected in audio"
            
            logger.info(f"✅ Transcription completed: {len(transcript)} characters")
            return transcript, None
            
        except Exception as e:
            logger.error(f"❌ Error during transcription: {str(e)}")
            return None, f"Transcription failed: {str(e)}"
    
    def process_video_file(self, video_path):
        """Complete video processing pipeline"""
        audio_path = None
        
        try:
            # Step 1: Extract audio
            audio_path, error = self.extract_audio_from_video(video_path)
            if error:
                return None, error
            
            # Step 2: Transcribe audio
            transcript, error = self.transcribe_audio(audio_path)
            if error:
                return None, error
            
            return transcript, None
            
        except Exception as e:
            logger.error(f"❌ Video processing pipeline failed: {str(e)}")
            return None, f"Video processing failed: {str(e)}"
            
        finally:
            # Always clean up temporary audio file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    logger.info("🧹 Temporary audio file cleaned up")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Could not clean up temp file: {str(cleanup_error)}")
    
    def validate_video_file(self, file_path):
        """Validate video file before processing"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, "Video file does not exist"
            
            # Check file extension
            ext = os.path.splitext(file_path)[1].lower()
            supported_formats = ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm']
            if ext not in supported_formats:
                return False, f"Unsupported format: {ext}. Supported: {', '.join(supported_formats)}"
            
            # Check file size (limit to 100MB)
            file_size = os.path.getsize(file_path)
            max_size = 100 * 1024 * 1024  # 100MB
            if file_size > max_size:
                return False, f"File too large: {file_size / (1024*1024):.1f}MB (max: 100MB)"
            
            # Try to open with MoviePy to check if it's a valid video
            try:
                video = VideoFileClip(file_path)
                duration = video.duration
                video.close()
                
                # Check duration (limit to 10 minutes for demo)
                if duration > 600:  # 10 minutes
                    return False, f"Video too long: {duration:.1f}s (max: 600s)"
                    
            except Exception as video_error:
                return False, f"Invalid video file: {str(video_error)}"
            
            return True, "Video file is valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_supported_formats(self):
        """Return list of supported video formats"""
        return ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm']
    
    def get_model_info(self):
        """Get information about the loaded model"""
        return {
            'model_name': self.model_name,
            'model_size': self.model_size,
            'device': 'GPU' if self.device >= 0 else 'CPU',
            'supported_formats': self.get_supported_formats()
        }
