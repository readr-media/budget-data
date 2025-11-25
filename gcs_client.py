"""Google Cloud Storage client for uploading JSON files."""

import json
import os
from typing import Any, Dict
from datetime import datetime
from google.cloud import storage
from config import settings


class GCSClient:
    """Client for uploading files to Google Cloud Storage."""
    
    def __init__(self):
        self.bucket_name = settings.gcs_bucket_name
        self.credentials_path = settings.gcs_credentials_path
        self.output_prefix = settings.gcs_output_prefix
        
        # Set credentials if provided
        if self.credentials_path and os.path.exists(self.credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
        
        self.client = None
        self.bucket = None
        
        if self.bucket_name:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize GCS client and bucket."""
        try:
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
        except Exception as e:
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
            raise Exception("GCS bucket not configured. Please set GCS_BUCKET_NAME environment variable.")
        
        # Add prefix to filename
        blob_name = f"{self.output_prefix}/{filename}"
        
        # Create blob
        blob = self.bucket.blob(blob_name)
        
        # Upload JSON data
        json_string = json.dumps(data, ensure_ascii=False, indent=2)
        blob.upload_from_string(
            json_string,
            content_type=content_type
        )
        
        # Make the blob publicly accessible (optional)
        # blob.make_public()
        
        return f"gs://{self.bucket_name}/{blob_name}"
    
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
