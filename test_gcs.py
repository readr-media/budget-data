import os
import logging
from gcs_client import gcs_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gcs_upload():
    """Test GCS upload functionality in isolation."""
    logger.info("Starting GCS upload test...")
    
    # Verify client initialization
    if gcs_client.client:
        logger.info(f"GCS Client initialized. Project ID: {gcs_client.client.project}")
    else:
        logger.warning("GCS Client not initialized (bucket name might be missing)")

    test_data = {
        "message": "This is a test upload from budget-data-api",
        "status": "success",
        "timestamp": "test_timestamp"
    }
    
    try:
        # Test upload
        logger.info("Attempting to upload test file...")
        url = gcs_client.upload_json(test_data, "test_upload.json")
        logger.info(f"Test upload successful! File URL: {url}")
        print(f"\nSUCCESS: File uploaded to {url}")
        
    except Exception as e:
        logger.error(f"Test upload failed: {e}")
        print(f"\nFAILURE: Upload failed. Error: {e}")

if __name__ == "__main__":
    # Check environment variables
    if not os.getenv("GCS_BUCKET_NAME"):
        print("WARNING: GCS_BUCKET_NAME not set in environment")
    
    test_gcs_upload()
