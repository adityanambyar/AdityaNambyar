from pydantic import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/meetnotes_india")
    
    # S3 Configuration
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_region: str = os.getenv("AWS_REGION", "ap-south-1")  # Mumbai region for India
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "meetnotes-india-audio")
    
    # OpenAI/Whisper Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # File Upload Limits
    max_file_size: int = 200 * 1024 * 1024  # 200MB
    allowed_audio_types: list = [
        "audio/mpeg",      # MP3
        "audio/mp4",       # M4A
        "audio/x-m4a",     # M4A alternative
        "audio/wav",       # WAV
        "audio/wave"       # WAV alternative
    ]
    
    # Auto-cleanup settings
    auto_delete_hours: int = 24
    cleanup_interval_minutes: int = 60  # Check every hour
    
    # Rate limiting and retry settings
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    
    # PDF Generation
    pdf_temp_dir: str = "/tmp/meetnotes_pdfs"
    
    class Config:
        env_file = ".env"

settings = Settings()