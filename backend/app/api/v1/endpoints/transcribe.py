from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import tempfile
from typing import Optional

from app.core.database import get_db, Meeting, Transcript
from app.services.s3_service import s3_service
from app.services.whisper_service import whisper_service

router = APIRouter()

@router.post("/{meeting_id}")
async def transcribe_audio(
    meeting_id: int,
    db: Session = Depends(get_db)
):
    """Transcribe audio using Whisper with verbose JSON output"""
    try:
        # Get meeting from database
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting.is_deleted:
            raise HTTPException(status_code=400, detail="Meeting has been deleted")
        
        # Check if transcript already exists
        existing_transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
        if existing_transcript:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Transcript already exists",
                    "meeting_id": meeting_id,
                    "transcript_id": existing_transcript.id,
                    "content": existing_transcript.content,
                    "language": existing_transcript.language,
                    "confidence": existing_transcript.confidence
                }
            )
        
        # Download audio from S3 to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(meeting.filename)[1]) as tmp_file:
            tmp_file_path = tmp_file.name
        
        try:
            # Download from S3
            await s3_service.download_file(meeting.s3_key, tmp_file_path)
            
            # Transcribe using Whisper
            transcription_result = await whisper_service.transcribe_audio(tmp_file_path)
            
            # Save transcript to database
            transcript = Transcript(
                meeting_id=meeting_id,
                content=transcription_result["text"],
                language=transcription_result["language"],
                confidence=int(transcription_result["confidence"] * 100)  # Convert to percentage
            )
            
            db.add(transcript)
            db.commit()
            db.refresh(transcript)
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            return JSONResponse(
                status_code=201,
                content={
                    "message": "Audio transcribed successfully",
                    "meeting_id": meeting_id,
                    "transcript_id": transcript.id,
                    "transcript": transcription_result,
                    "language": transcription_result["language"],
                    "confidence": transcription_result["confidence"],
                    "duration": transcription_result.get("duration", 0),
                    "segments_count": len(transcription_result.get("segments", []))
                }
            )
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

@router.get("/{meeting_id}")
async def get_transcript(
    meeting_id: int,
    db: Session = Depends(get_db)
):
    """Get transcript for a meeting"""
    try:
        # Get meeting from database
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting.is_deleted:
            raise HTTPException(status_code=400, detail="Meeting has been deleted")
        
        # Get transcript
        transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        return JSONResponse(
            status_code=200,
            content={
                "meeting_id": meeting_id,
                "transcript_id": transcript.id,
                "content": transcript.content,
                "language": transcript.language,
                "confidence": transcript.confidence,
                "created_at": transcript.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve transcript: {str(e)}"
        )

@router.get("/{meeting_id}/verbose")
async def get_verbose_transcript(
    meeting_id: int,
    db: Session = Depends(get_db)
):
    """Get verbose transcript with segments and timestamps"""
    try:
        # Get meeting from database
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting.is_deleted:
            raise HTTPException(status_code=400, detail="Meeting has been deleted")
        
        # Get transcript
        transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        # For verbose output, we need to re-transcribe to get segments
        # This is a limitation of storing only the text in the database
        # In production, you might want to store the full verbose output
        
        return JSONResponse(
            status_code=200,
            content={
                "meeting_id": meeting_id,
                "transcript_id": transcript.id,
                "content": transcript.content,
                "language": transcript.language,
                "confidence": transcript.confidence,
                "created_at": transcript.created_at.isoformat(),
                "note": "For full verbose output with segments, use POST /transcribe/{meeting_id}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve verbose transcript: {str(e)}"
        )