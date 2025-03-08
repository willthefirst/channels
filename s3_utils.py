"""
Utility functions for AWS S3 operations.
"""
import os
import logging
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from typing import Optional, BinaryIO, Tuple, List

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")  # Optional, for custom endpoints

# Application settings
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
ALLOWED_VIDEO_EXTENSIONS = os.getenv("ALLOWED_VIDEO_EXTENSIONS", ".mp4,.webm,.mov,.avi,.mkv").split(",")

def get_s3_client():
    """
    Create and return an S3 client.
    """
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
            endpoint_url=S3_ENDPOINT_URL
        )
        return s3_client
    except Exception as e:
        logger.error(f"Failed to create S3 client: {e}")
        raise

def upload_file_to_s3(file_obj: BinaryIO, filename: str, content_type: str) -> Tuple[bool, str]:
    """
    Upload a file to S3 bucket.
    
    Args:
        file_obj: File-like object to upload
        filename: Name to give the file in S3
        content_type: MIME type of the file
        
    Returns:
        Tuple of (success, url_or_error_message)
    """
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
        return False, "S3 credentials not configured"
    
    try:
        s3_client = get_s3_client()
        
        # Upload the file
        s3_client.upload_fileobj(
            file_obj,
            S3_BUCKET_NAME,
            filename,
            ExtraArgs={
                'ContentType': content_type,
                'ACL': 'public-read'  # Make the file publicly accessible
            }
        )
        
        # Generate the URL for the uploaded file
        if S3_ENDPOINT_URL:
            # Custom endpoint
            url = f"{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{filename}"
        else:
            # Standard AWS S3 URL format
            url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{filename}"
        
        logger.info(f"Successfully uploaded {filename} to S3")
        return True, url
    
    except ClientError as e:
        error_message = f"S3 upload error: {str(e)}"
        logger.error(error_message)
        return False, error_message
    except Exception as e:
        error_message = f"Unexpected error during S3 upload: {str(e)}"
        logger.error(error_message)
        return False, error_message

def list_videos_from_s3() -> List[dict]:
    """
    List all videos in the S3 bucket.
    
    Returns:
        List of dictionaries with video information
    """
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
        logger.error("S3 credentials not configured")
        return []
    
    try:
        s3_client = get_s3_client()
        
        # List objects in the bucket
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)
        
        videos = []
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                # Check if it's a video file
                if any(key.lower().endswith(ext) for ext in ALLOWED_VIDEO_EXTENSIONS):
                    # Generate URL
                    if S3_ENDPOINT_URL:
                        url = f"{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{key}"
                    else:
                        url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
                    
                    videos.append({
                        "url": url,
                        "key": key,
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat()
                    })
        
        return videos
    
    except ClientError as e:
        logger.error(f"S3 list error: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error listing S3 objects: {str(e)}")
        return []

def is_valid_video_file(filename: str) -> bool:
    """
    Check if the file has an allowed video extension.
    """
    return any(filename.lower().endswith(ext) for ext in ALLOWED_VIDEO_EXTENSIONS)

def delete_video_from_s3(key: str) -> Tuple[bool, str]:
    """
    Delete a video from the S3 bucket.
    
    Args:
        key: The S3 object key to delete
        
    Returns:
        Tuple of (success, message)
    """
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
        return False, "S3 credentials not configured"
    
    try:
        s3_client = get_s3_client()
        
        # Delete the object
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=key)
        
        logger.info(f"Successfully deleted {key} from S3")
        return True, f"Successfully deleted {key}"
    
    except ClientError as e:
        error_message = f"S3 delete error: {str(e)}"
        logger.error(error_message)
        return False, error_message
    except Exception as e:
        error_message = f"Unexpected error during S3 delete: {str(e)}"
        logger.error(error_message)
        return False, error_message 