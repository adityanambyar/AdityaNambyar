from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
import uuid
from datetime import datetime

class MeetingRecord(Base):
    __tablename__ = "meeting_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    s3_url = Column(String(500), nullable=True)
    
    # Timestamps
    upload_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    auto_delete_time = Column(DateTime, nullable=False)
    
    # Processing results
    transcript = Column(JSON, nullable=True)  # Whisper verbose_json format
    summary = Column(JSON, nullable=True)     # Structured summary
    
    # Processing status
    transcription_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    summarization_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Privacy and cleanup
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<MeetingRecord(id={self.id}, title='{self.title}', upload_time={self.upload_time})>"