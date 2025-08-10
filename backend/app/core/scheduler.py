import asyncio
import logging
from datetime import datetime, timedelta
from app.core.background import cleanup_expired_audio

logger = logging.getLogger(__name__)

class AudioCleanupScheduler:
    def __init__(self):
        self.task = None
        self.running = False
        self.cleanup_interval = 3600  # Run cleanup every hour
    
    async def start(self):
        """Start the cleanup scheduler"""
        if self.running:
            logger.info("Cleanup scheduler already running")
            return
        
        self.running = True
        logger.info("Starting audio cleanup scheduler")
        
        while self.running:
            try:
                await cleanup_expired_audio()
                await asyncio.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"Error in cleanup scheduler: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    def stop(self):
        """Stop the cleanup scheduler"""
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info("Audio cleanup scheduler stopped")
    
    async def run_once(self):
        """Run cleanup once immediately"""
        await cleanup_expired_audio()

# Global scheduler instance
scheduler = AudioCleanupScheduler()

def start_scheduler():
    """Start the background scheduler"""
    try:
        scheduler.task = asyncio.create_task(scheduler.start())
        logger.info("Background scheduler started")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")

def stop_scheduler():
    """Stop the background scheduler"""
    try:
        scheduler.stop()
        logger.info("Background scheduler stopped")
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {str(e)}")