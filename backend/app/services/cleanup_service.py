import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models import MeetingRecord
from ..database import SessionLocal
from ..config import settings
from .upload_service import UploadService

logger = logging.getLogger(__name__)

class CleanupService:
    def __init__(self):
        self.upload_service = UploadService()
    
    async def schedule_cleanup(self):
        """Schedule periodic cleanup of expired meetings"""
        while True:
            try:
                await self._cleanup_expired_meetings()
                # Wait for next cleanup cycle
                await asyncio.sleep(settings.cleanup_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Cleanup scheduler error: {str(e)}")
                # Wait a bit before retrying
                await asyncio.sleep(300)  # 5 minutes
    
    async def _cleanup_expired_meetings(self):
        """Clean up meetings that have passed their auto-delete time"""
        db = SessionLocal()
        try:
            current_time = datetime.utcnow()
            
            # Find meetings that should be deleted
            expired_meetings = db.query(MeetingRecord).filter(
                and_(
                    MeetingRecord.auto_delete_time <= current_time,
                    MeetingRecord.is_deleted == False
                )
            ).all()
            
            logger.info(f"Found {len(expired_meetings)} expired meetings to clean up")
            
            for meeting in expired_meetings:
                try:
                    await self.delete_meeting(meeting, db)
                    logger.info(f"Auto-deleted meeting: {meeting.id}")
                except Exception as e:
                    logger.error(f"Failed to auto-delete meeting {meeting.id}: {str(e)}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Cleanup process failed: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    async def delete_meeting(self, meeting: MeetingRecord, db: Session):
        """
        Delete a meeting and all associated data
        - Remove audio file from S3
        - Mark as deleted in database
        - Clear sensitive data
        """
        try:
            # Delete audio file from S3
            if meeting.s3_url:
                deletion_success = await self.upload_service.delete_from_s3(meeting.s3_url)
                if not deletion_success:
                    logger.warning(f"Failed to delete S3 file for meeting {meeting.id}")
            
            # Clear sensitive data and mark as deleted
            meeting.is_deleted = True
            meeting.deleted_at = datetime.utcnow()
            meeting.s3_url = None
            meeting.transcript = None
            meeting.summary = None
            
            # Keep basic metadata for audit purposes
            # meeting.title and meeting.upload_time remain for record keeping
            
            db.commit()
            
            logger.info(f"Meeting {meeting.id} successfully deleted")
            
        except Exception as e:
            logger.error(f"Failed to delete meeting {meeting.id}: {str(e)}")
            db.rollback()
            raise e
    
    async def extend_meeting_lifetime(self, meeting_id: str, hours: int, db: Session) -> bool:
        """
        Extend the auto-delete time for a meeting
        Useful for important meetings that need to be kept longer
        """
        try:
            meeting = db.query(MeetingRecord).filter(MeetingRecord.id == meeting_id).first()
            if not meeting:
                return False
            
            if meeting.is_deleted:
                return False
            
            # Extend the auto-delete time
            meeting.auto_delete_time = meeting.auto_delete_time + timedelta(hours=hours)
            db.commit()
            
            logger.info(f"Extended lifetime for meeting {meeting_id} by {hours} hours")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extend meeting lifetime {meeting_id}: {str(e)}")
            db.rollback()
            return False
    
    async def get_cleanup_stats(self, db: Session) -> dict:
        """Get statistics about cleanup operations"""
        try:
            current_time = datetime.utcnow()
            
            # Count meetings by status
            total_meetings = db.query(MeetingRecord).count()
            active_meetings = db.query(MeetingRecord).filter(MeetingRecord.is_deleted == False).count()
            deleted_meetings = db.query(MeetingRecord).filter(MeetingRecord.is_deleted == True).count()
            
            # Count meetings expiring soon (next 24 hours)
            expiring_soon = db.query(MeetingRecord).filter(
                and_(
                    MeetingRecord.auto_delete_time <= current_time + timedelta(hours=24),
                    MeetingRecord.auto_delete_time > current_time,
                    MeetingRecord.is_deleted == False
                )
            ).count()
            
            # Count overdue meetings (should have been deleted but weren't)
            overdue_meetings = db.query(MeetingRecord).filter(
                and_(
                    MeetingRecord.auto_delete_time <= current_time,
                    MeetingRecord.is_deleted == False
                )
            ).count()
            
            return {
                "total_meetings": total_meetings,
                "active_meetings": active_meetings,
                "deleted_meetings": deleted_meetings,
                "expiring_soon_24h": expiring_soon,
                "overdue_deletions": overdue_meetings,
                "last_cleanup_check": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get cleanup stats: {str(e)}")
            return {
                "error": "Failed to retrieve cleanup statistics"
            }