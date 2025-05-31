from fastapi import APIRouter
from backend.app.services.s3_service import generate_presigned_url

router = APIRouter()


@router.get("/generate-presigned-url")
def get_presigned_url(file_name: str):
    """
    API endpoint to generate a pre-signed URL for uploading files to S3.

    :param file_name: The name of the file to be uploaded.
    :return: JSON response containing the pre-signed URL.
    """
    url = generate_presigned_url(file_name)
    print(url)
    return url
