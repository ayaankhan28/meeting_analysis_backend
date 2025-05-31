# fetch_video.py

import boto3
from backend.app.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME

def download_video_from_s3(object_key, local_path):
    """Download a video file from S3."""
    s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
    try:
        s3.download_file(S3_BUCKET_NAME, object_key, local_path)
        print(f"Video downloaded to {local_path}")
    except Exception as e:
        print(f"Error downloading video: {e}")

# download_video_from_s3("test/videoplayback.mp4", "videoplayback.mp4")