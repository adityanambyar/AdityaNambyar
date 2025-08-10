import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Meeting
from app.services.s3_service import s3_service
from app.core.config import settings

logger = logging.getLogger(__name__)

async def cleanup_expired_audio():
    """Clean up expired audio files from S3 and database"""
    try:
        db = SessionLocal()
        try:
            # Find expired meetings
            current_time = datetime.utcnow()
            expired_meetings = db.query(Meeting).filter(
                Meeting.expires_at <= current_time,
                Meeting.is_deleted == False
            ).all()
            
            if not expired_meetings:
                logger.info("No expired audio files found")
                return
            
            logger.info(f"Found {len(expired_meetings)} expired audio files to clean up")
            
            for meeting in expired_meetings:
                try:
                    # Delete from S3
                    await s3_service.delete_file(meeting.s3_key)
                    
                    # Mark as deleted in database
                    meeting.is_deleted = True
                    
                    logger.info(f"Cleaned up expired audio file: {meeting.original_filename}")
                    
                except Exception as e:
                    logger.error(f"Failed to clean up audio file {meeting.original_filename}: {str(e)}")
                    # Continue with other files even if one fails
            
            # Commit all changes
            db.commit()
            logger.info(f"Successfully cleaned up {len(expired_meetings)} expired audio files")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in cleanup_expired_audio: {str(e)}")

async def cleanup_single_meeting(meeting_id: int):
    """Clean up a specific meeting by ID"""
    try:
        db = SessionLocal()
        try:
            meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
            if not meeting:
                logger.warning(f"Meeting {meeting_id} not found for cleanup")
                return False
            
            if meeting.is_deleted:
                logger.info(f"Meeting {meeting_id} already deleted")
                return True
            
            # Delete from S3
            await s3_service.delete_file(meeting.s3_key)
            
            # Mark as deleted in database
            meeting.is_deleted = True
            db.commit()
            
            logger.info(f"Successfully cleaned up meeting {meeting_id}")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error cleaning up meeting {meeting_id}: {str(e)}")
        return False