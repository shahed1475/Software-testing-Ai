"""
Storage manager for handling test artifacts with database integration.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from .minio_client import MinIOClient, get_minio_client
from ..database import DatabaseManager, TestArtifact, get_db


logger = logging.getLogger(__name__)


class StorageManager:
    """Manages test artifacts storage with database tracking."""
    
    def __init__(self, 
                 minio_client: Optional[MinIOClient] = None,
                 db_manager: Optional[DatabaseManager] = None):
        """
        Initialize storage manager.
        
        Args:
            minio_client: MinIO client instance
            db_manager: Database manager instance
        """
        self.minio_client = minio_client or get_minio_client()
        self.db_manager = db_manager
    
    def store_test_artifact(self,
                           test_run_id: int,
                           file_path: str,
                           artifact_type: str,
                           name: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> Optional[TestArtifact]:
        """
        Store a test artifact and create database record.
        
        Args:
            test_run_id: ID of the test run
            file_path: Path to the artifact file
            artifact_type: Type of artifact (screenshot, video, report, etc.)
            name: Custom name for the artifact
            metadata: Additional metadata
            
        Returns:
            TestArtifact record if successful
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Artifact file not found: {file_path}")
                return None
            
            # Determine bucket type based on artifact type
            bucket_type = self._get_bucket_type(artifact_type)
            
            # Generate object name
            if name is None:
                name = Path(file_path).name
            
            # Prepare tags and metadata for MinIO
            tags = {
                'test_run_id': str(test_run_id),
                'artifact_type': artifact_type,
                'upload_date': datetime.utcnow().strftime('%Y-%m-%d')
            }
            
            minio_metadata = {
                'test_run_id': str(test_run_id),
                'artifact_type': artifact_type,
                'original_name': name
            }
            
            if metadata:
                minio_metadata.update({k: str(v) for k, v in metadata.items()})
            
            # Upload to MinIO
            object_url = self.minio_client.upload_file(
                bucket_type=bucket_type,
                file_path=file_path,
                object_name=name,
                metadata=minio_metadata,
                tags=tags
            )
            
            # Create database record
            if self.db_manager:
                with self.db_manager.get_session() as session:
                    artifact = TestArtifact(
                        test_run_id=test_run_id,
                        name=name,
                        type=artifact_type,
                        file_path=object_url,
                        file_size=os.path.getsize(file_path),
                        metadata=metadata or {}
                    )
                    
                    session.add(artifact)
                    session.commit()
                    session.refresh(artifact)
                    
                    logger.info(f"Stored artifact: {name} for test run {test_run_id}")
                    return artifact
            
            logger.info(f"Uploaded artifact to MinIO: {object_url}")
            return None
            
        except Exception as e:
            logger.error(f"Error storing artifact {file_path}: {e}")
            return None
    
    def store_test_data(self,
                       test_run_id: int,
                       data: bytes,
                       filename: str,
                       artifact_type: str,
                       content_type: str = "application/octet-stream",
                       metadata: Optional[Dict[str, Any]] = None) -> Optional[TestArtifact]:
        """
        Store test data directly and create database record.
        
        Args:
            test_run_id: ID of the test run
            data: Data to store
            filename: Name for the file
            artifact_type: Type of artifact
            content_type: Content type of the data
            metadata: Additional metadata
            
        Returns:
            TestArtifact record if successful
        """
        try:
            # Determine bucket type
            bucket_type = self._get_bucket_type(artifact_type)
            
            # Prepare tags and metadata for MinIO
            tags = {
                'test_run_id': str(test_run_id),
                'artifact_type': artifact_type,
                'upload_date': datetime.utcnow().strftime('%Y-%m-%d')
            }
            
            minio_metadata = {
                'test_run_id': str(test_run_id),
                'artifact_type': artifact_type,
                'original_name': filename,
                'content_type': content_type
            }
            
            if metadata:
                minio_metadata.update({k: str(v) for k, v in metadata.items()})
            
            # Upload to MinIO
            object_url = self.minio_client.upload_data(
                bucket_type=bucket_type,
                data=data,
                object_name=filename,
                content_type=content_type,
                metadata=minio_metadata,
                tags=tags
            )
            
            # Create database record
            if self.db_manager:
                with self.db_manager.get_session() as session:
                    artifact = TestArtifact(
                        test_run_id=test_run_id,
                        name=filename,
                        type=artifact_type,
                        file_path=object_url,
                        file_size=len(data),
                        metadata=metadata or {}
                    )
                    
                    session.add(artifact)
                    session.commit()
                    session.refresh(artifact)
                    
                    logger.info(f"Stored data artifact: {filename} for test run {test_run_id}")
                    return artifact
            
            logger.info(f"Uploaded data to MinIO: {object_url}")
            return None
            
        except Exception as e:
            logger.error(f"Error storing data artifact {filename}: {e}")
            return None
    
    def get_artifact(self, artifact_id: int) -> Optional[TestArtifact]:
        """
        Get artifact by ID.
        
        Args:
            artifact_id: Artifact ID
            
        Returns:
            TestArtifact record if found
        """
        if not self.db_manager:
            return None
        
        try:
            with self.db_manager.get_session() as session:
                return session.query(TestArtifact).filter_by(id=artifact_id).first()
        except Exception as e:
            logger.error(f"Error getting artifact {artifact_id}: {e}")
            return None
    
    def get_test_run_artifacts(self, test_run_id: int) -> List[TestArtifact]:
        """
        Get all artifacts for a test run.
        
        Args:
            test_run_id: Test run ID
            
        Returns:
            List of TestArtifact records
        """
        if not self.db_manager:
            return []
        
        try:
            with self.db_manager.get_session() as session:
                return session.query(TestArtifact).filter_by(test_run_id=test_run_id).all()
        except Exception as e:
            logger.error(f"Error getting artifacts for test run {test_run_id}: {e}")
            return []
    
    def download_artifact(self, artifact_id: int, local_path: str) -> bool:
        """
        Download an artifact to local path.
        
        Args:
            artifact_id: Artifact ID
            local_path: Local path to save the file
            
        Returns:
            True if successful
        """
        artifact = self.get_artifact(artifact_id)
        if not artifact:
            logger.error(f"Artifact {artifact_id} not found")
            return False
        
        try:
            # Extract bucket type and object name from URL
            bucket_type, object_name = self._parse_artifact_url(artifact.file_path)
            
            return self.minio_client.download_file(
                bucket_type=bucket_type,
                object_name=object_name,
                file_path=local_path
            )
            
        except Exception as e:
            logger.error(f"Error downloading artifact {artifact_id}: {e}")
            return False
    
    def get_artifact_data(self, artifact_id: int) -> Optional[bytes]:
        """
        Get artifact data directly.
        
        Args:
            artifact_id: Artifact ID
            
        Returns:
            Artifact data as bytes
        """
        artifact = self.get_artifact(artifact_id)
        if not artifact:
            logger.error(f"Artifact {artifact_id} not found")
            return None
        
        try:
            # Extract bucket type and object name from URL
            bucket_type, object_name = self._parse_artifact_url(artifact.file_path)
            
            return self.minio_client.get_object_data(
                bucket_type=bucket_type,
                object_name=object_name
            )
            
        except Exception as e:
            logger.error(f"Error getting artifact data {artifact_id}: {e}")
            return None
    
    def get_artifact_url(self, artifact_id: int, expires_hours: int = 1) -> Optional[str]:
        """
        Get presigned URL for an artifact.
        
        Args:
            artifact_id: Artifact ID
            expires_hours: URL expiration in hours
            
        Returns:
            Presigned URL
        """
        artifact = self.get_artifact(artifact_id)
        if not artifact:
            logger.error(f"Artifact {artifact_id} not found")
            return None
        
        try:
            from datetime import timedelta
            
            # Extract bucket type and object name from URL
            bucket_type, object_name = self._parse_artifact_url(artifact.file_path)
            
            return self.minio_client.get_presigned_url(
                bucket_type=bucket_type,
                object_name=object_name,
                expires=timedelta(hours=expires_hours)
            )
            
        except Exception as e:
            logger.error(f"Error getting artifact URL {artifact_id}: {e}")
            return None
    
    def delete_artifact(self, artifact_id: int) -> bool:
        """
        Delete an artifact from storage and database.
        
        Args:
            artifact_id: Artifact ID
            
        Returns:
            True if successful
        """
        artifact = self.get_artifact(artifact_id)
        if not artifact:
            logger.error(f"Artifact {artifact_id} not found")
            return False
        
        try:
            # Extract bucket type and object name from URL
            bucket_type, object_name = self._parse_artifact_url(artifact.file_path)
            
            # Delete from MinIO
            minio_success = self.minio_client.delete_object(
                bucket_type=bucket_type,
                object_name=object_name
            )
            
            # Delete from database
            if self.db_manager:
                with self.db_manager.get_session() as session:
                    session.delete(artifact)
                    session.commit()
            
            logger.info(f"Deleted artifact {artifact_id}")
            return minio_success
            
        except Exception as e:
            logger.error(f"Error deleting artifact {artifact_id}: {e}")
            return False
    
    def cleanup_old_artifacts(self, days_old: int = 30) -> Dict[str, int]:
        """
        Clean up old artifacts from storage.
        
        Args:
            days_old: Delete artifacts older than this many days
            
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            'artifacts_deleted': 0,
            'reports_deleted': 0,
            'screenshots_deleted': 0,
            'videos_deleted': 0,
            'security_deleted': 0
        }
        
        try:
            # Clean up each bucket type
            for bucket_type in ['artifacts', 'reports', 'screenshots', 'videos', 'security']:
                deleted = self.minio_client.cleanup_old_objects(
                    bucket_type=bucket_type,
                    days_old=days_old
                )
                stats[f'{bucket_type}_deleted'] = deleted
            
            # Clean up database records for deleted artifacts
            if self.db_manager:
                from datetime import datetime, timedelta
                cutoff_date = datetime.utcnow() - timedelta(days=days_old)
                
                with self.db_manager.get_session() as session:
                    old_artifacts = session.query(TestArtifact).filter(
                        TestArtifact.created_at < cutoff_date
                    ).all()
                    
                    for artifact in old_artifacts:
                        # Check if the MinIO object still exists
                        try:
                            bucket_type, object_name = self._parse_artifact_url(artifact.file_path)
                            data = self.minio_client.get_object_data(bucket_type, object_name)
                            if data is None:
                                # Object doesn't exist in MinIO, remove from database
                                session.delete(artifact)
                        except:
                            # Error accessing object, remove from database
                            session.delete(artifact)
                    
                    session.commit()
            
            logger.info(f"Cleanup completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return stats
    
    def _get_bucket_type(self, artifact_type: str) -> str:
        """
        Determine MinIO bucket type based on artifact type.
        
        Args:
            artifact_type: Type of artifact
            
        Returns:
            Bucket type
        """
        type_mapping = {
            'screenshot': 'screenshots',
            'video': 'videos',
            'report': 'reports',
            'html_report': 'reports',
            'json_report': 'reports',
            'xml_report': 'reports',
            'security_report': 'security',
            'log': 'artifacts',
            'trace': 'artifacts',
            'coverage': 'artifacts'
        }
        
        return type_mapping.get(artifact_type.lower(), 'artifacts')
    
    def _parse_artifact_url(self, url: str) -> tuple[str, str]:
        """
        Parse artifact URL to extract bucket type and object name.
        
        Args:
            url: Artifact URL
            
        Returns:
            Tuple of (bucket_type, object_name)
        """
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError(f"Invalid artifact URL: {url}")
        
        bucket_name = path_parts[0]
        object_name = '/'.join(path_parts[1:])
        
        # Map bucket name to bucket type
        bucket_type_mapping = {v: k for k, v in self.minio_client.buckets.items()}
        bucket_type = bucket_type_mapping.get(bucket_name, 'artifacts')
        
        return bucket_type, object_name


# Global storage manager instance
_storage_manager: Optional[StorageManager] = None


def get_storage_manager(db_manager: Optional[DatabaseManager] = None) -> StorageManager:
    """Get or create storage manager instance."""
    global _storage_manager
    
    if _storage_manager is None:
        _storage_manager = StorageManager(db_manager=db_manager)
    
    return _storage_manager