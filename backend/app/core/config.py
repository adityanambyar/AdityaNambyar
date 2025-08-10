from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "MeetNotes India"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://meetnotes-india.onrender.com",
        "https://meetnotes-india.fly.dev"
    ]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/meetnotes")
    
    # S3 Storage
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "meetnotes-audio")
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", None)
    
    # File Upload
    MAX_FILE_SIZE: int = 200 * 1024 * 1024  # 200MB
    ALLOWED_AUDIO_TYPES: List[str] = ["audio/m4a", "audio/mp3", "audio/wav", "audio/mpeg"]
    
    # Whisper Settings
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    WHISPER_LANGUAGE: str = os.getenv("WHISPER_LANGUAGE", "auto")
    
    # Privacy Settings
    AUDIO_RETENTION_HOURS: int = 24
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()