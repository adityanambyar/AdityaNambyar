import whisper
import os
import tempfile
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.services.translation_service import TranslationService
import json

logger = logging.getLogger(__name__)

class WhisperService:
    def __init__(self):
        self.model = whisper.load_model(settings.WHISPER_MODEL)
        self.translation_service = TranslationService()
    
    async def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio using Whisper with verbose JSON output"""
        try:
            # Transcribe with verbose JSON output
            result = self.model.transcribe(
                audio_path,
                verbose=True,
                language=settings.WHISPER_LANGUAGE,
                task="transcribe"
            )
            
            # Process segments for better timestamping
            processed_segments = []
            for segment in result.get("segments", []):
                processed_segment = {
                    "start": segment.get("start", 0),
                    "end": segment.get("end", 0),
                    "text": segment.get("text", "").strip(),
                    "confidence": segment.get("avg_logprob", 0)
                }
                processed_segments.append(processed_segment)
            
            # Detect language and add glosses for Indian languages
            detected_language = result.get("language", "unknown")
            if detected_language in ["ta", "hi"]:  # Tamil or Hindi
                processed_segments = await self._add_english_glosses(
                    processed_segments, detected_language
                )
            
            return {
                "text": result.get("text", "").strip(),
                "language": detected_language,
                "segments": processed_segments,
                "confidence": result.get("avg_logprob", 0),
                "duration": result.get("duration", 0)
            }
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise
    
    async def _add_english_glosses(
        self, segments: list, source_language: str
    ) -> list:
        """Add English glosses for Tamil/Hindi text"""
        try:
            for segment in segments:
                original_text = segment["text"]
                if source_language == "ta":  # Tamil
                    english_gloss = await self.translation_service.translate(
                        original_text, "ta", "en"
                    )
                    if english_gloss:
                        segment["text"] = f"{original_text} ({english_gloss})"
                        segment["english_gloss"] = english_gloss
                
                elif source_language == "hi":  # Hindi
                    english_gloss = await self.translation_service.translate(
                        original_text, "hi", "en"
                    )
                    if english_gloss:
                        segment["text"] = f"{original_text} ({english_gloss})"
                        segment["english_gloss"] = english_gloss
            
            return segments
            
        except Exception as e:
            logger.error(f"Error adding English glosses: {str(e)}")
            return segments
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return ["en", "ta", "hi", "auto"]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded Whisper model"""
        return {
            "model_name": settings.WHISPER_MODEL,
            "supported_languages": self.get_supported_languages(),
            "max_audio_length": "30 minutes"  # Whisper base model limit
        }

whisper_service = WhisperService()