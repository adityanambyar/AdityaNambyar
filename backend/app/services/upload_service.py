import boto3
import aiofiles
import tempfile
import os
import re
from fastapi import HTTPException, UploadFile
from botocore.exceptions import ClientError
import magic
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class UploadService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
    
    def validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file:
        - Check MIME type
        - Check file size
        - Sanitize filename
        """
        # Check file size
        if hasattr(file, 'size') and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size // (1024*1024)}MB"
            )
        
        # Check MIME type
        if file.content_type not in settings.allowed_audio_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed types: {', '.join(settings.allowed_audio_types)}"
            )
        
        # Sanitize filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
            
        self._sanitize_filename(file.filename)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent security issues"""
        # Remove path separators and special characters
        sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Ensure it's not empty after sanitization
        if not sanitized or sanitized == '.':
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:250] + ext
        
        return sanitized
    
    async def upload_to_s3(self, file: UploadFile, meeting_id: str) -> str:
        """
        Upload file to S3 bucket
        Returns S3 URL
        """
        try:
            # Create sanitized filename with meeting ID
            sanitized_filename = self._sanitize_filename(file.filename)
            s3_key = f"audio/{meeting_id}/{sanitized_filename}"
            
            # Read file content
            file_content = await file.read()
            
            # Validate actual file content with python-magic
            file_mime = magic.from_buffer(file_content, mime=True)
            if file_mime not in settings.allowed_audio_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"File content doesn't match declared type. Detected: {file_mime}"
                )
            
            # Reset file position for re-reading if needed
            await file.seek(0)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type,
                Metadata={
                    'meeting_id': str(meeting_id),
                    'original_filename': file.filename,
                    'upload_time': str(int(time.time()))
                }
            )
            
            # Generate S3 URL
            s3_url = f"s3://{settings.s3_bucket_name}/{s3_key}"
            
            logger.info(f"File uploaded to S3: {s3_url}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to upload file to storage")
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            raise HTTPException(status_code=500, detail="File upload failed")
    
    async def delete_from_s3(self, s3_url: str) -> bool:
        """Delete file from S3"""
        try:
            # Extract key from S3 URL
            s3_key = s3_url.replace(f"s3://{settings.s3_bucket_name}/", "")
            
            self.s3_client.delete_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key
            )
            
            logger.info(f"File deleted from S3: {s3_url}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 deletion failed: {str(e)}")
            return False
    
    def generate_presigned_url(self, s3_url: str, expiration: int = 3600) -> str:
        """Generate presigned URL for S3 object"""
        try:
            s3_key = s3_url.replace(f"s3://{settings.s3_bucket_name}/", "")
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.s3_bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate download URL")

import time