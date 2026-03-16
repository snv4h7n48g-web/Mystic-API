"""
S3 service for palm image uploads.
Handles pre-signed URLs and image storage.
"""

import boto3
import os
import uuid
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class S3Service:
    """Service for managing palm image uploads to S3."""
    
    def __init__(self):
        """Initialize S3 client."""
        # Get credentials from environment
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Build client kwargs
        client_kwargs = {
            'service_name': 's3',
            'region_name': region
        }
        
        # Only add explicit credentials if they're set
        if aws_access_key and aws_access_key != 'your_access_key_here':
            client_kwargs['aws_access_key_id'] = aws_access_key
            client_kwargs['aws_secret_access_key'] = aws_secret_key
        
        self.client = boto3.client(**client_kwargs)
        
        # S3 bucket configuration
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'mystic-palm-images')
        self.bucket_region = region
    
    def generate_presigned_upload_url(
        self,
        session_id: str,
        content_type: str = "image/jpeg",
        expires_in: int = 300,
        prefix: str = "palms"
    ) -> Dict[str, str]:
        """
        Generate a pre-signed URL for direct client upload.
        
        Args:
            session_id: Session identifier
            content_type: MIME type of the image
            expires_in: URL expiration in seconds (default 5 minutes)
            
        Returns:
            Dict with upload_url and object_key
        """
        # Generate unique object key
        image_id = str(uuid.uuid4())
        object_key = f"{prefix}/{session_id}/{image_id}.jpg"
        
        try:
            # Generate pre-signed POST URL
            presigned_post = self.client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=object_key,
                Fields={
                    "Content-Type": content_type
                },
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 100, 10485760]  # 100 bytes to 10MB
                ],
                ExpiresIn=expires_in
            )
            
            return {
                "upload_url": presigned_post['url'],
                "upload_fields": presigned_post['fields'],
                "object_key": object_key,
                "expires_in": expires_in
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate upload URL: {str(e)}")
    
    def generate_presigned_download_url(
        self,
        object_key: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a pre-signed URL for downloading an image.
        
        Args:
            object_key: S3 object key
            expires_in: URL expiration in seconds (default 1 hour)
            
        Returns:
            Pre-signed download URL
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expires_in
            )
            return url
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate download URL: {str(e)}")
    
    def get_image_bytes(self, object_key: str) -> bytes:
        """
        Download image bytes from S3.
        
        Args:
            object_key: S3 object key
            
        Returns:
            Image bytes
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return response['Body'].read()
            
        except Exception as e:
            raise RuntimeError(f"Failed to download image: {str(e)}")
    
    def delete_image(self, object_key: str) -> bool:
        """
        Delete an image from S3.
        
        Args:
            object_key: S3 object key
            
        Returns:
            True if successful
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
            
        except Exception as e:
            raise RuntimeError(f"Failed to delete image: {str(e)}")


# Singleton instance
_s3_service = None

def get_s3_service() -> S3Service:
    """Get or create singleton S3 service."""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
