from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json
from typing import Optional

from app.core.database import get_db, Meeting, Transcript, Summary
from app.services.summarization_service import summarization_service

router = APIRouter()

def _parse_action_items(action_items_json: Optional[str]) -> list:
    """Parse action items JSON from database"""
    if not action_items_json:
        return []
    
    try:
        return json.loads(action_items_json)
    except json.JSONDecodeError:
        return []

@router.post("/{meeting_id}")
async def summarize_meeting(
    meeting_id: int,
    db: Session = Depends(get_db)
):
    """Generate meeting summary with decisions, action items, and WhatsApp blurb"""
    try:
        # Get meeting from database
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting.is_deleted:
            raise HTTPException(status_code=400, detail="Meeting has been deleted")
        
        # Check if summary already exists
        existing_summary = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
        if existing_summary:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Summary already exists",
                    "meeting_id": meeting_id,
                    "summary_id": existing_summary.id,
                    "summary": {
                        "decisions": existing_summary.decisions.split('\n') if existing_summary.decisions else [],
                        "action_items": _parse_action_items(existing_summary.action_items),
                        "open_questions": existing_summary.open_questions.split('\n') if existing_summary.open_questions else [],
                        "whatsapp_blurb": existing_summary.whatsapp_blurb
                    }
                }
            )
        
        # Get transcript
        transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
        if not transcript:
            raise HTTPException(
                status_code=400, 
                detail="Transcript not found. Please transcribe the audio first."
            )
        
        # Generate summary
        summary_result = await summarization_service.summarize_transcript(
            transcript.content, transcript.language
        )
        
        # Save summary to database
        summary = Summary(
            meeting_id=meeting_id,
            decisions='\n'.join(summary_result["decisions"]) if summary_result["decisions"] else None,
            action_items=json.dumps(summary_result["action_items"]) if summary_result["action_items"] else None,
            open_questions='\n'.join(summary_result["open_questions"]) if summary_result["open_questions"] else None,
            whatsapp_blurb=summary_result["whatsapp_blurb"]
        )
        
        db.add(summary)
        db.commit()
        db.refresh(summary)
        
        return JSONResponse(
            status_code=201,
            content={
                "message": "Meeting summary generated successfully",
                "meeting_id": meeting_id,
                "summary_id": summary.id,
                "summary": summary_result,
                "language": transcript.language,
                "transcript_length": len(transcript.content)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Summary generation failed: {str(e)}"
        )

@router.get("/{meeting_id}")
async def get_summary(
    meeting_id: int,
    db: Session = Depends(get_db)
):
    """Get meeting summary"""
    try:
        # Get meeting from database
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting.is_deleted:
            raise HTTPException(status_code=400, detail="Meeting has been deleted")
        
        # Get summary
        summary = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
        if not summary:
            raise HTTPException(status_code=404, detail="Summary not found")
        
        return JSONResponse(
            status_code=200,
            content={
                "meeting_id": meeting_id,
                "summary_id": summary.id,
                "summary": {
                    "decisions": summary.decisions.split('\n') if summary.decisions else [],
                    "action_items": _parse_action_items(summary.action_items),
                    "open_questions": summary.open_questions.split('\n') if summary.open_questions else [],
                    "whatsapp_blurb": summary.whatsapp_blurb
                },
                "created_at": summary.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve summary: {str(e)}"
        )

@router.get("/{meeting_id}/whatsapp")
async def get_whatsapp_summary(
    meeting_id: int,
    db: Session = Depends(get_db)
):
    """Get WhatsApp-ready summary blurb"""
    try:
        # Get meeting from database
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting.is_deleted:
            raise HTTPException(status_code=400, detail="Meeting has been deleted")
        
        # Get summary
        summary = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
        if not summary:
            raise HTTPException(status_code=404, detail="Summary not found")
        
        return JSONResponse(
            status_code=200,
            content={
                "meeting_id": meeting_id,
                "whatsapp_blurb": summary.whatsapp_blurb,
                "character_count": len(summary.whatsapp_blurb) if summary.whatsapp_blurb else 0,
                "created_at": summary.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve WhatsApp summary: {str(e)}"
        )