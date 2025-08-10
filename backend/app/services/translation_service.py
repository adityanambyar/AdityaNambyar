from googletrans import Translator
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.translator = Translator()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> Optional[str]:
        """Translate text with exponential backoff retry"""
        try:
            if not text or len(text.strip()) == 0:
                return None
            
            # Clean the text
            cleaned_text = text.strip()
            
            # Perform translation
            result = self.translator.translate(
                cleaned_text,
                src=source_lang,
                dest=target_lang
            )
            
            if result and result.text:
                return result.text.strip()
            return None
            
        except Exception as e:
            logger.error(f"Translation error ({source_lang} -> {target_lang}): {str(e)}")
            return None
    
    async def add_gloss_to_text(
        self, text: str, source_language: str
    ) -> str:
        """Add English gloss to Tamil/Hindi text"""
        if source_language not in ["ta", "hi"]:
            return text
        
        try:
            english_gloss = await self.translate(text, source_language, "en")
            if english_gloss:
                return f"{text} ({english_gloss})"
            return text
        except Exception as e:
            logger.error(f"Error adding gloss: {str(e)}")
            return text
    
    def get_supported_languages(self) -> dict:
        """Get supported language codes"""
        return {
            "ta": "Tamil",
            "hi": "Hindi", 
            "en": "English",
            "auto": "Auto-detect"
        }
    
    async def detect_language(self, text: str) -> Optional[str]:
        """Detect the language of the given text"""
        try:
            if not text or len(text.strip()) == 0:
                return None
            
            result = self.translator.detect(text.strip())
            if result and result.lang:
                return result.lang
            return None
            
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            return None

translation_service = TranslationService()