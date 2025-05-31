import boto3
from botocore.exceptions import NoCredentialsError
from backend.app.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

def generate_presigned_url(file_name: str, expiration: int = 3600):
    """
    Generate a pre-signed URL to upload a file to S3.

    :param file_name: The name of the file to be uploaded.
    :param expiration: URL expiration time in seconds (default 1 hour).
    :return: A dictionary containing the pre-signed URL.
    """
    try:
        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": file_name, "ContentType": "application/octet-stream"},
            ExpiresIn=expiration,
        )
        return {"url": presigned_url}
    except NoCredentialsError:
        return {"error": "AWS credentials not found"}
