import openai
import requests
import asyncio
import logging
import json
import re
from typing import Dict, Any
from sqlalchemy.orm import Session
from ..models import MeetingRecord
from ..config import settings
from .upload_service import UploadService

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.upload_service = UploadService()
        
        # Indian language patterns for preservation
        self.indian_language_patterns = {
            'tamil': re.compile(r'[\u0B80-\u0BFF]+'),
            'hindi': re.compile(r'[\u0900-\u097F]+'),
            'devanagari': re.compile(r'[\u0900-\u097F]+')
        }
    
    async def transcribe_audio(self, meeting_id: str, s3_url: str, db: Session) -> None:
        """
        Transcribe audio using Whisper API with verbose_json format
        Preserves Tamil/Hindi text with English glosses
        """
        meeting = db.query(MeetingRecord).filter(MeetingRecord.id == meeting_id).first()
        if not meeting:
            logger.error(f"Meeting not found: {meeting_id}")
            return
        
        try:
            # Update status to processing
            meeting.transcription_status = "processing"
            db.commit()
            
            # Get presigned URL for audio file
            audio_url = self.upload_service.generate_presigned_url(s3_url)
            
            # Download audio file temporarily
            audio_response = requests.get(audio_url)
            audio_response.raise_for_status()
            
            # Use Whisper API with exponential backoff
            transcript_data = await self._transcribe_with_retry(audio_response.content, meeting.original_filename)
            
            # Process and enhance transcript for Indian languages
            enhanced_transcript = self._enhance_indian_language_transcript(transcript_data)
            
            # Save transcript
            meeting.transcript = enhanced_transcript
            meeting.transcription_status = "completed"
            db.commit()
            
            logger.info(f"Transcription completed for meeting: {meeting_id}")
            
        except Exception as e:
            logger.error(f"Transcription failed for meeting {meeting_id}: {str(e)}")
            meeting.transcription_status = "failed"
            db.commit()
    
    async def _transcribe_with_retry(self, audio_content: bytes, filename: str) -> Dict[str, Any]:
        """Transcribe with exponential backoff retry logic"""
        max_retries = settings.max_retries
        base_delay = settings.base_delay
        max_delay = settings.max_delay
        
        for attempt in range(max_retries):
            try:
                # Create temporary file for API call
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                    temp_file.write(audio_content)
                    temp_file.flush()
                    
                    # Call Whisper API
                    with open(temp_file.name, "rb") as audio_file:
                        transcript = self.openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="verbose_json",
                            language="en",  # Primary language, but Whisper can detect others
                            timestamp_granularities=["word", "segment"]
                        )
                
                # Clean up temp file
                import os
                os.unlink(temp_file.name)
                
                return transcript.model_dump()
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(f"Transcription attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                await asyncio.sleep(delay)
        
        raise Exception(f"Transcription failed after {max_retries} attempts")
    
    def _enhance_indian_language_transcript(self, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance transcript to preserve Indian language text with English glosses
        """
        enhanced_data = transcript_data.copy()
        
        # Process main text
        if 'text' in enhanced_data:
            enhanced_data['text'] = self._add_language_glosses(enhanced_data['text'])
        
        # Process segments if available
        if 'segments' in enhanced_data:
            for segment in enhanced_data['segments']:
                if 'text' in segment:
                    segment['text'] = self._add_language_glosses(segment['text'])
                
                # Process words if available
                if 'words' in segment:
                    for word in segment['words']:
                        if 'word' in word:
                            word['word'] = self._add_language_glosses(word['word'])
        
        # Add language detection metadata
        enhanced_data['detected_languages'] = self._detect_languages(transcript_data.get('text', ''))
        enhanced_data['india_enhanced'] = True
        
        return enhanced_data
    
    def _add_language_glosses(self, text: str) -> str:
        """Add English glosses in parentheses for Indian language text"""
        enhanced_text = text
        
        # Find Tamil text and add glosses
        tamil_matches = self.indian_language_patterns['tamil'].findall(text)
        for tamil_text in tamil_matches:
            # This is a simplified approach - in production, you'd use a proper translation service
            gloss = self._get_simple_gloss(tamil_text, 'tamil')
            if gloss and gloss != tamil_text:
                enhanced_text = enhanced_text.replace(
                    tamil_text, 
                    f"{tamil_text} ({gloss})"
                )
        
        # Find Hindi text and add glosses
        hindi_matches = self.indian_language_patterns['hindi'].findall(text)
        for hindi_text in hindi_matches:
            gloss = self._get_simple_gloss(hindi_text, 'hindi')
            if gloss and gloss != hindi_text:
                enhanced_text = enhanced_text.replace(
                    hindi_text, 
                    f"{hindi_text} ({gloss})"
                )
        
        return enhanced_text
    
    def _get_simple_gloss(self, text: str, language: str) -> str:
        """
        Get a simple English gloss for Indian language text
        In production, this would use a proper translation API
        """
        # Common greetings and phrases
        common_phrases = {
            'hindi': {
                'नमस्ते': 'hello',
                'धन्यवाद': 'thank you',
                'अच्छा': 'good',
                'बहुत अच्छा': 'very good',
                'समझ गया': 'understood',
                'ठीक है': 'okay'
            },
            'tamil': {
                'வணக்கம்': 'hello',
                'நன்றி': 'thank you',
                'நல்லது': 'good',
                'புரியுது': 'understood',
                'சரி': 'okay'
            }
        }
        
        if language in common_phrases and text in common_phrases[language]:
            return common_phrases[language][text]
        
        # For other text, return a placeholder or use a translation service
        return f"[{language} text]"
    
    def _detect_languages(self, text: str) -> Dict[str, bool]:
        """Detect which Indian languages are present in the text"""
        languages = {}
        
        for lang, pattern in self.indian_language_patterns.items():
            languages[lang] = bool(pattern.search(text))
        
        return languages