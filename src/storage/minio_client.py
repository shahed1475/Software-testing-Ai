"""
MinIO client for artifact storage management.
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, BinaryIO
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error
from minio.commonconfig import Tags


logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO client for managing test artifacts and reports."""
    
    def __init__(self, 
                 endpoint: str = "localhost:9000",
                 access_key: str = "minioadmin",
                 secret_key: str = "minioadmin123",
                 secure: bool = False):
        """
        Initialize MinIO client.
        
        Args:
            endpoint: MinIO server endpoint
            access_key: Access key for authentication
            secret_key: Secret key for authentication
            secure: Whether to use HTTPS
        """
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        
        # Default buckets
        self.buckets = {
            'artifacts': 'test-artifacts',
            'reports': 'test-reports',
            'screenshots': 'test-screenshots',
            'videos': 'test-videos',
            'security': 'security-reports'
        }
        
        self._ensure_buckets_exist()
    
    def _ensure_buckets_exist(self):
        """Ensure all required buckets exist."""
        try:
            for bucket_name in self.buckets.values():
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
                    logger.info(f"Created bucket: {bucket_name}")
        except S3Error as e:
            logger.error(f"Error creating buckets: {e}")
    
    def upload_file(self, 
                   bucket_type: str,
                   file_path: str,
                   object_name: Optional[str] = None,
                   metadata: Optional[Dict[str, str]] = None,
                   tags: Optional[Dict[str, str]] = None) -> str:
        """
        Upload a file to MinIO.
        
        Args:
            bucket_type: Type of bucket (artifacts, reports, screenshots, videos, security)
            file_path: Path to the file to upload
            object_name: Object name in bucket (defaults to filename)
            metadata: Additional metadata for the object
            tags: Tags for the object
            
        Returns:
            Object URL
        """
        if bucket_type not in self.buckets:
            raise ValueError(f"Invalid bucket type: {bucket_type}")
        
        bucket_name = self.buckets[bucket_type]
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if object_name is None:
            object_name = Path(file_path).name
        
        # Add timestamp prefix to avoid conflicts
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        object_name = f"{timestamp}_{object_name}"
        
        try:
            # Prepare metadata
            file_metadata = metadata or {}
            file_metadata.update({
                'upload_time': datetime.utcnow().isoformat(),
                'original_path': file_path,
                'file_size': str(os.path.getsize(file_path))
            })
            
            # Prepare tags
            file_tags = Tags()
            if tags:
                for key, value in tags.items():
                    file_tags[key] = value
            
            # Upload file
            result = self.client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path,
                metadata=file_metadata,
                tags=file_tags
            )
            
            # Generate URL
            url = self._get_object_url(bucket_name, object_name)
            
            logger.info(f"Uploaded {file_path} to {url}")
            return url
            
        except S3Error as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            raise
    
    def upload_data(self,
                   bucket_type: str,
                   data: bytes,
                   object_name: str,
                   content_type: str = "application/octet-stream",
                   metadata: Optional[Dict[str, str]] = None,
                   tags: Optional[Dict[str, str]] = None) -> str:
        """
        Upload data directly to MinIO.
        
        Args:
            bucket_type: Type of bucket
            data: Data to upload
            object_name: Object name in bucket
            content_type: Content type of the data
            metadata: Additional metadata
            tags: Tags for the object
            
        Returns:
            Object URL
        """
        if bucket_type not in self.buckets:
            raise ValueError(f"Invalid bucket type: {bucket_type}")
        
        bucket_name = self.buckets[bucket_type]
        
        # Add timestamp prefix
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        object_name = f"{timestamp}_{object_name}"
        
        try:
            from io import BytesIO
            
            # Prepare metadata
            file_metadata = metadata or {}
            file_metadata.update({
                'upload_time': datetime.utcnow().isoformat(),
                'data_size': str(len(data))
            })
            
            # Prepare tags
            file_tags = Tags()
            if tags:
                for key, value in tags.items():
                    file_tags[key] = value
            
            # Upload data
            result = self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=BytesIO(data),
                length=len(data),
                content_type=content_type,
                metadata=file_metadata,
                tags=file_tags
            )
            
            # Generate URL
            url = self._get_object_url(bucket_name, object_name)
            
            logger.info(f"Uploaded data to {url}")
            return url
            
        except S3Error as e:
            logger.error(f"Error uploading data: {e}")
            raise
    
    def download_file(self, 
                     bucket_type: str,
                     object_name: str,
                     file_path: str) -> bool:
        """
        Download a file from MinIO.
        
        Args:
            bucket_type: Type of bucket
            object_name: Object name in bucket
            file_path: Local path to save the file
            
        Returns:
            True if successful
        """
        if bucket_type not in self.buckets:
            raise ValueError(f"Invalid bucket type: {bucket_type}")
        
        bucket_name = self.buckets[bucket_type]
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Download file
            self.client.fget_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path
            )
            
            logger.info(f"Downloaded {object_name} to {file_path}")
            return True
            
        except S3Error as e:
            logger.error(f"Error downloading file {object_name}: {e}")
            return False
    
    def get_object_data(self, bucket_type: str, object_name: str) -> Optional[bytes]:
        """
        Get object data directly.
        
        Args:
            bucket_type: Type of bucket
            object_name: Object name in bucket
            
        Returns:
            Object data as bytes
        """
        if bucket_type not in self.buckets:
            raise ValueError(f"Invalid bucket type: {bucket_type}")
        
        bucket_name = self.buckets[bucket_type]
        
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            return data
            
        except S3Error as e:
            logger.error(f"Error getting object data {object_name}: {e}")
            return None
    
    def list_objects(self, 
                    bucket_type: str,
                    prefix: str = "",
                    recursive: bool = True) -> List[Dict[str, Any]]:
        """
        List objects in a bucket.
        
        Args:
            bucket_type: Type of bucket
            prefix: Object name prefix filter
            recursive: Whether to list recursively
            
        Returns:
            List of object information
        """
        if bucket_type not in self.buckets:
            raise ValueError(f"Invalid bucket type: {bucket_type}")
        
        bucket_name = self.buckets[bucket_type]
        objects = []
        
        try:
            for obj in self.client.list_objects(bucket_name, prefix=prefix, recursive=recursive):
                objects.append({
                    'name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.etag,
                    'url': self._get_object_url(bucket_name, obj.object_name)
                })
            
            return objects
            
        except S3Error as e:
            logger.error(f"Error listing objects: {e}")
            return []
    
    def delete_object(self, bucket_type: str, object_name: str) -> bool:
        """
        Delete an object from MinIO.
        
        Args:
            bucket_type: Type of bucket
            object_name: Object name to delete
            
        Returns:
            True if successful
        """
        if bucket_type not in self.buckets:
            raise ValueError(f"Invalid bucket type: {bucket_type}")
        
        bucket_name = self.buckets[bucket_type]
        
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"Deleted object: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Error deleting object {object_name}: {e}")
            return False
    
    def get_presigned_url(self, 
                         bucket_type: str,
                         object_name: str,
                         expires: timedelta = timedelta(hours=1)) -> Optional[str]:
        """
        Generate a presigned URL for an object.
        
        Args:
            bucket_type: Type of bucket
            object_name: Object name
            expires: URL expiration time
            
        Returns:
            Presigned URL
        """
        if bucket_type not in self.buckets:
            raise ValueError(f"Invalid bucket type: {bucket_type}")
        
        bucket_name = self.buckets[bucket_type]
        
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=expires
            )
            
            return url
            
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
    
    def _get_object_url(self, bucket_name: str, object_name: str) -> str:
        """Generate object URL."""
        protocol = "https" if self.secure else "http"
        return f"{protocol}://{self.endpoint}/{bucket_name}/{object_name}"
    
    def cleanup_old_objects(self, 
                           bucket_type: str,
                           days_old: int = 30,
                           prefix: str = "") -> int:
        """
        Clean up objects older than specified days.
        
        Args:
            bucket_type: Type of bucket
            days_old: Delete objects older than this many days
            prefix: Object name prefix filter
            
        Returns:
            Number of objects deleted
        """
        if bucket_type not in self.buckets:
            raise ValueError(f"Invalid bucket type: {bucket_type}")
        
        bucket_name = self.buckets[bucket_type]
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        deleted_count = 0
        
        try:
            for obj in self.client.list_objects(bucket_name, prefix=prefix, recursive=True):
                if obj.last_modified < cutoff_date:
                    self.client.remove_object(bucket_name, obj.object_name)
                    deleted_count += 1
                    logger.info(f"Deleted old object: {obj.object_name}")
            
            logger.info(f"Cleaned up {deleted_count} old objects from {bucket_name}")
            return deleted_count
            
        except S3Error as e:
            logger.error(f"Error during cleanup: {e}")
            return deleted_count


# Global MinIO client instance
_minio_client: Optional[MinIOClient] = None


def get_minio_client() -> MinIOClient:
    """Get or create MinIO client instance."""
    global _minio_client
    
    if _minio_client is None:
        # Get configuration from environment variables
        endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
        secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        _minio_client = MinIOClient(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
    
    return _minio_client