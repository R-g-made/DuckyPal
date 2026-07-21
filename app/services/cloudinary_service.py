import cloudinary
import cloudinary.uploader
import os
from app.core.config import settings

class CloudinaryService:
    def __init__(self):
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )

    async def upload_image(self, file_path: str, public_id: str = None) -> str:
        """
        Uploads an image to Cloudinary and returns the secure URL.
        """
        try:
            response = cloudinary.uploader.upload(
                file_path,
                public_id=public_id,
                folder="utyapal/analysis"
            )
            return response.get("secure_url")
        except Exception as e:
            import logging
            logging.error(f"Cloudinary upload error: {e}")
            return None

cloudinary_service = CloudinaryService()
