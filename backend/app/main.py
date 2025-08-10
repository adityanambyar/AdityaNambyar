from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import logging
from typing import Optional
import asyncio
from datetime import datetime, timedelta

from .database import get_db, init_db
from .models import MeetingRecord
from .services.upload_service import UploadService
from .services.transcription_service import TranscriptionService
from .services.summary_service import SummaryService
from .services.pdf_service import PDFService
from .services.cleanup_service import CleanupService
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MeetNotes India",
    description="AI-powered meeting transcription and summarization for India",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
upload_service = UploadService()
transcription_service = TranscriptionService()
summary_service = SummaryService()
pdf_service = PDFService()
cleanup_service = CleanupService()

@app.on_event("startup")
async def startup_event():
    """Initialize database and start cleanup scheduler"""
    init_db()
    # Start background cleanup task
    asyncio.create_task(cleanup_service.schedule_cleanup())

@app.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Upload audio file (≤200MB; M4A/MP3/WAV)
    Returns meeting record ID for tracking
    """
    try:
        # Validate file
        upload_service.validate_file(file)
        
        # Create meeting record
        meeting = MeetingRecord(
            title=title or f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            original_filename=file.filename,
            upload_time=datetime.utcnow(),
            auto_delete_time=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)
        
        # Upload to S3
        s3_url = await upload_service.upload_to_s3(file, meeting.id)
        meeting.s3_url = s3_url
        db.commit()
        
        logger.info(f"Audio uploaded successfully: {meeting.id}")
        
        return {
            "meeting_id": meeting.id,
            "message": "File uploaded successfully",
            "auto_delete_time": meeting.auto_delete_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/transcribe")
async def transcribe_audio(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Transcribe audio using Whisper API with verbose_json format
    Preserves Tamil/Hindi text with English glosses
    """
    try:
        meeting = db.query(MeetingRecord).filter(MeetingRecord.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
            
        if not meeting.s3_url:
            raise HTTPException(status_code=400, detail="No audio file found")
            
        if meeting.transcript:
            return {
                "meeting_id": meeting_id,
                "transcript": meeting.transcript,
                "message": "Transcript already exists"
            }
        
        # Start transcription in background
        background_tasks.add_task(
            transcription_service.transcribe_audio,
            meeting_id,
            meeting.s3_url,
            db
        )
        
        return {
            "meeting_id": meeting_id,
            "message": "Transcription started",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/summarize")
async def summarize_transcript(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate AI summary with:
    - Decisions made
    - Action items (Owner, Due date)
    - Open questions
    - WhatsApp blurb (≤900 chars)
    """
    try:
        meeting = db.query(MeetingRecord).filter(MeetingRecord.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
            
        if not meeting.transcript:
            raise HTTPException(status_code=400, detail="No transcript found. Please transcribe first.")
            
        if meeting.summary:
            return {
                "meeting_id": meeting_id,
                "summary": meeting.summary,
                "message": "Summary already exists"
            }
        
        # Start summarization in background
        background_tasks.add_task(
            summary_service.generate_summary,
            meeting_id,
            meeting.transcript,
            db
        )
        
        return {
            "meeting_id": meeting_id,
            "message": "Summarization started",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Summarization failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/minutes/{meeting_id}/pdf")
async def generate_pdf(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """
    Generate timestamped PDF of meeting minutes
    """
    try:
        meeting = db.query(MeetingRecord).filter(MeetingRecord.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
            
        if not meeting.transcript or not meeting.summary:
            raise HTTPException(
                status_code=400, 
                detail="Both transcript and summary are required for PDF generation"
            )
        
        # Generate PDF
        pdf_path = await pdf_service.generate_pdf(meeting)
        
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"meeting_{meeting_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/meeting/{meeting_id}")
async def get_meeting(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Get meeting details including transcript and summary status"""
    try:
        meeting = db.query(MeetingRecord).filter(MeetingRecord.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
            
        return {
            "meeting_id": meeting.id,
            "title": meeting.title,
            "upload_time": meeting.upload_time.isoformat(),
            "auto_delete_time": meeting.auto_delete_time.isoformat(),
            "has_transcript": bool(meeting.transcript),
            "has_summary": bool(meeting.summary),
            "transcript": meeting.transcript,
            "summary": meeting.summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get meeting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/meeting/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Delete meeting and associated files immediately"""
    try:
        meeting = db.query(MeetingRecord).filter(MeetingRecord.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
            
        # Delete from S3 and database
        await cleanup_service.delete_meeting(meeting, db)
        
        return {"message": "Meeting deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete meeting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)