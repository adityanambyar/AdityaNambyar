from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import tempfile
import uuid
from datetime import datetime, timedelta
import mimetypes
import re
from typing import Optional

from app.core.database import get_db
from app.core.config import settings
from app.services.s3_service import s3_service
from app.core.database import Meeting

router = APIRouter()

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent security issues"""
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    # Ensure filename is not empty
    if not filename:
        filename = "audio_file"
    return filename

def validate_audio_file(file: UploadFile) -> bool:
    """Validate audio file type and size"""
    # Check file size
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size {file.size} bytes exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Check MIME type
    if file.content_type not in settings.ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(settings.ALLOWED_AUDIO_TYPES)}"
        )
    
    # Additional validation for file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = ['.m4a', '.mp3', '.wav']
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File extension {file_extension} not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
        )
    
    return True

@router.post("/")
async def upload_audio(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload audio file for transcription"""
    try:
        # Validate file
        validate_audio_file(file)
        
        # Sanitize filename
        original_filename = file.filename
        safe_filename = sanitize_filename(original_filename)
        
        # Generate unique filename
        file_extension = os.path.splitext(safe_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            # Read file content in chunks to handle large files
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Upload to S3
            s3_key = f"audio/{unique_filename}"
            await s3_service.upload_file(tmp_file_path, s3_key)
            
            # Calculate expiration time (24 hours from now)
            expires_at = datetime.utcnow() + timedelta(hours=settings.AUDIO_RETENTION_HOURS)
            
            # Save to database
            meeting = Meeting(
                filename=unique_filename,
                original_filename=original_filename,
                file_size=len(content),
                mime_type=file.content_type,
                s3_key=s3_key,
                expires_at=expires_at
            )
            
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            return JSONResponse(
                status_code=201,
                content={
                    "message": "Audio file uploaded successfully",
                    "meeting_id": meeting.id,
                    "filename": unique_filename,
                    "original_filename": original_filename,
                    "file_size": len(content),
                    "expires_at": expires_at.isoformat(),
                    "s3_key": s3_key
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
            detail=f"Internal server error: {str(e)}"
        )

@router.delete("/{meeting_id}")
async def delete_audio(
    meeting_id: int,
    db: Session = Depends(get_db)
):
    """Delete audio file immediately"""
    try:
        # Get meeting from database
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting.is_deleted:
            raise HTTPException(status_code=400, detail="Meeting already deleted")
        
        # Delete from S3
        await s3_service.delete_file(meeting.s3_key)
        
        # Mark as deleted in database
        meeting.is_deleted = True
        db.commit()
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Audio file deleted successfully",
                "meeting_id": meeting_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )