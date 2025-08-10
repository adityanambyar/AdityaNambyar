from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import json
from typing import Optional

from app.core.database import get_db, Meeting, Transcript, Summary
from app.services.pdf_service import pdf_service

router = APIRouter()

def _parse_action_items(action_items_json: Optional[str]) -> list:
    """Parse action items JSON from database"""
    if not action_items_json:
        return []
    
    try:
        return json.loads(action_items_json)
    except json.JSONDecodeError:
        return []

@router.get("/{meeting_id}/pdf")
async def generate_meeting_minutes_pdf(
    meeting_id: int,
    db: Session = Depends(get_db)
):
    """Generate and download timestamped PDF meeting minutes"""
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
            raise HTTPException(
                status_code=400, 
                detail="Transcript not found. Please transcribe the audio first."
            )
        
        # Get summary
        summary = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
        if not summary:
            raise HTTPException(
                status_code=400, 
                detail="Summary not found. Please generate summary first."
            )
        
        # Prepare data for PDF generation
        meeting_data = {
            "id": meeting.id,
            "filename": meeting.filename,
            "original_filename": meeting.original_filename,
            "file_size": meeting.file_size,
            "mime_type": meeting.mime_type,
            "uploaded_at": meeting.uploaded_at.isoformat() if meeting.uploaded_at else "N/A",
            "expires_at": meeting.expires_at.isoformat() if meeting.expires_at else "N/A",
            "is_deleted": meeting.is_deleted
        }
        
        transcript_data = {
            "text": transcript.content,
            "language": transcript.language,
            "confidence": transcript.confidence,
            "segments": []  # We'll need to store segments in the future for better PDFs
        }
        
        summary_data = {
            "decisions": summary.decisions.split('\n') if summary.decisions else [],
            "action_items": _parse_action_items(summary.action_items),
            "open_questions": summary.open_questions.split('\n') if summary.open_questions else [],
            "whatsapp_blurb": summary.whatsapp_blurb
        }
        
        # Generate PDF
        pdf_path = await pdf_service.generate_meeting_minutes(
            meeting_data, transcript_data, summary_data
        )
        
        # Return PDF file
        filename = f"meeting_minutes_{meeting_id}_{meeting.original_filename}.pdf"
        
        return FileResponse(
            path=pdf_path,
            filename=filename,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )

@router.get("/{meeting_id}/preview")
async def preview_meeting_minutes(
    meeting_id: int,
    db: Session = Depends(get_db)
):
    """Preview meeting minutes data without generating PDF"""
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
            raise HTTPException(
                status_code=400, 
                detail="Transcript not found. Please transcribe the audio first."
            )
        
        # Get summary
        summary = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
        if not summary:
            raise HTTPException(
                status_code=400, 
                detail="Summary not found. Please generate summary first."
            )
        
        return {
            "meeting_id": meeting_id,
            "meeting": {
                "id": meeting.id,
                "original_filename": meeting.original_filename,
                "file_size": meeting.file_size,
                "uploaded_at": meeting.uploaded_at.isoformat() if meeting.uploaded_at else "N/A",
                "expires_at": meeting.expires_at.isoformat() if meeting.expires_at else "N/A"
            },
            "transcript": {
                "language": transcript.language,
                "confidence": transcript.confidence,
                "content_preview": transcript.content[:500] + "..." if len(transcript.content) > 500 else transcript.content
            },
            "summary": {
                "decisions_count": len(summary.decisions.split('\n')) if summary.decisions else 0,
                "action_items_count": len(_parse_action_items(summary.action_items)),
                "open_questions_count": len(summary.open_questions.split('\n')) if summary.open_questions else 0,
                "whatsapp_blurb_preview": summary.whatsapp_blurb[:200] + "..." if summary.whatsapp_blurb and len(summary.whatsapp_blurb) > 200 else summary.whatsapp_blurb
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to preview meeting minutes: {str(e)}"
        )