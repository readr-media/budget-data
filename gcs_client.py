"""Google Cloud Storage client for uploading JSON files."""

import json
import os
from typing import Any, Dict
from datetime import datetime
from google.cloud import storage
from config import settings


import logging

# Configure logging
logger = logging.getLogger(__name__)


class GCSClient:
    """Client for uploading files to Google Cloud Storage."""
    
    def __init__(self):
        self.bucket_name = settings.gcs_bucket_name
        self.credentials_path = settings.gcs_credentials_path
        self.output_prefix = settings.gcs_output_prefix
        
        logger.info(f"Initializing GCS Client. Bucket: {self.bucket_name}, Prefix: {self.output_prefix}")
        
        # Set credentials if provided
        if self.credentials_path and os.path.exists(self.credentials_path):
            logger.info(f"Using credentials from: {self.credentials_path}")
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
        else:
            logger.info("No credentials path provided or file not found. Using default credentials.")
        
        self.client = None
        self.bucket = None
        
        if self.bucket_name:
            self._initialize_client()
        else:
            logger.warning("GCS_BUCKET_NAME not set. Uploads will fail.")
    
    def _initialize_client(self):
        """Initialize GCS client and bucket."""
        try:
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
            
            # Log project ID to verify credentials
            logger.info(f"GCS Client initialized. Project ID: {self.client.project}")
            
            # Verify bucket existence/access
            if self.bucket.exists():
                logger.info(f"Successfully verified access to bucket: {self.bucket_name}")
            else:
                logger.error(f"Bucket {self.bucket_name} does not exist or access is denied.")
                
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}", exc_info=True)
            raise Exception(f"Failed to initialize GCS client: {e}")
    
    def upload_json(self, data: Any, filename: str, content_type: str = "application/json") -> str:
        """
        Upload JSON data to GCS.
        
        Args:
            data: Data to upload (will be JSON serialized)
            filename: Name of the file in GCS
            content_type: Content type of the file
            
        Returns:
            Public URL of the uploaded file
        """
        if not self.bucket:
            logger.error("Attempted upload but GCS bucket not configured")
            raise Exception("GCS bucket not configured. Please set GCS_BUCKET_NAME environment variable.")
        
        # Add prefix to filename
        blob_name = f"{self.output_prefix}/{filename}"
        
        logger.info(f"Starting upload to gs://{self.bucket_name}/{blob_name}")
        
        try:
            # Create blob
            blob = self.bucket.blob(blob_name)
            
            # Serialize JSON data
            json_string = json.dumps(data, ensure_ascii=False, indent=2)
            data_size = len(json_string.encode('utf-8'))
            logger.info(f"Serialized JSON size: {data_size} bytes")
            
            # Upload JSON data
            logger.info(f"[{datetime.now()}] Beginning upload_from_string...")
            blob.upload_from_string(
                json_string,
                content_type=content_type,
                timeout=60  # Explicit timeout for upload
            )
            logger.info(f"[{datetime.now()}] upload_from_string completed.")
            
            logger.info(f"Upload complete: gs://{self.bucket_name}/{blob_name}")
            return f"gs://{self.bucket_name}/{blob_name}"
            
        except Exception as e:
            logger.error(f"Failed to upload to GCS: {str(e)}", exc_info=True)
            # Check for common GCS errors
            if "403" in str(e):
                logger.error("Permission denied. Check service account permissions.")
            elif "404" in str(e):
                logger.error("Bucket or path not found.")
            raise Exception(f"GCS Upload failed: {str(e)}")
    
    def upload_statistics(self, stats_type: str, data: Any) -> str:
        """
        Upload statistics JSON to GCS with timestamped filename.
        
        Args:
            stats_type: Type of statistics ('by-legislator' or 'by-department')
            data: Statistics data to upload
            
        Returns:
            GCS path of the uploaded file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{stats_type}_{timestamp}.json"
        
        return self.upload_json(data, filename)
    
    def upload_latest_statistics(self, stats_type: str, data: Any) -> str:
        """
        Upload statistics JSON to GCS with a fixed 'latest' filename.
        This will overwrite the previous 'latest' file.
        
        Args:
            stats_type: Type of statistics ('by-legislator' or 'by-department')
            data: Statistics data to upload
            
        Returns:
            GCS path of the uploaded file
        """
        filename = f"{stats_type}_latest.json"
        
        return self.upload_json(data, filename)


# Global GCS client instance
gcs_client = GCSClient()
