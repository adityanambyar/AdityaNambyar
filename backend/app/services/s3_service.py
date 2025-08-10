import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from tenacity import retry, stop_after_attempt, wait_exponential
import os
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def upload_file(self, file_path: str, s3_key: str) -> bool:
        """Upload a file to S3 with exponential backoff retry"""
        try:
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ContentType': 'audio/mpeg'}
            )
            logger.info(f"Successfully uploaded {file_path} to S3 as {s3_key}")
            return True
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"Failed to upload {file_path} to S3: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3 with exponential backoff retry"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Successfully deleted {s3_key} from S3")
            return True
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"Failed to delete {s3_key} from S3: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def download_file(self, s3_key: str, local_path: str) -> bool:
        """Download a file from S3 with exponential backoff retry"""
        try:
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )
            logger.info(f"Successfully downloaded {s3_key} to {local_path}")
            return True
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"Failed to download {s3_key} from S3: {str(e)}")
            raise
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate a presigned URL for temporary access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {str(e)}")
            return None

s3_service = S3Service()