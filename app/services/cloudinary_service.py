import os
import logging
from typing import Optional

logger = logging.getLogger("agroguard.cloudinary_service")

try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    logger.warning("cloudinary package not installed. Run: pip install cloudinary")


class CloudinaryService:
    """
    Handles upload of crop scan images to Cloudinary CDN.
    Activated automatically when CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY,
    and CLOUDINARY_API_SECRET environment variables are set.
    Falls back to local disk storage silently if credentials are absent.
    """

    _configured = False

    @classmethod
    def configure(cls):
        """Configure cloudinary SDK from environment variables (called once at startup)."""
        if cls._configured or not CLOUDINARY_AVAILABLE:
            return
        from ..config import settings
        if settings.USE_CLOUDINARY:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True
            )
            cls._configured = True
            logger.info(
                f"Cloudinary configured: cloud_name={settings.CLOUDINARY_CLOUD_NAME}. "
                "Images will be stored on Cloudinary CDN."
            )
        else:
            logger.info("Cloudinary credentials not set. Using local disk upload fallback.")

    @classmethod
    def upload_image(cls, file_path: str, public_id: str) -> Optional[str]:
        """
        Upload a local image file to Cloudinary.

        Args:
            file_path:  Absolute path to the locally saved temp image file.
            public_id:  Unique identifier for the image on Cloudinary
                        (e.g. "agroguard/scans/s_abc123").

        Returns:
            Cloudinary secure HTTPS URL string on success, or None on failure.
        """
        if not CLOUDINARY_AVAILABLE or not cls._configured:
            return None
        try:
            result = cloudinary.uploader.upload(
                file_path,
                public_id=public_id,
                folder="agroguard/scans",
                overwrite=True,
                resource_type="image",
                transformation=[
                    # Resize to max 1200px wide to save storage, keep aspect ratio
                    {"width": 1200, "crop": "limit"},
                    # Auto quality optimisation
                    {"quality": "auto:good"},
                    {"fetch_format": "auto"}
                ]
            )
            url: str = result.get("secure_url", "")
            logger.info(f"Uploaded scan image to Cloudinary: {url}")
            return url
        except Exception as e:
            logger.error(f"Cloudinary upload failed for {public_id}: {str(e)}")
            return None

    @classmethod
    def delete_image(cls, public_id: str) -> bool:
        """
        Delete an image from Cloudinary by its public_id.

        Args:
            public_id:  The public_id used when uploading (without folder prefix
                        if folder was specified separately).

        Returns:
            True if deleted successfully, False otherwise.
        """
        if not CLOUDINARY_AVAILABLE or not cls._configured:
            return False
        try:
            result = cloudinary.uploader.destroy(f"agroguard/scans/{public_id}")
            success = result.get("result") == "ok"
            if success:
                logger.info(f"Deleted Cloudinary image: agroguard/scans/{public_id}")
            return success
        except Exception as e:
            logger.error(f"Cloudinary delete failed for {public_id}: {str(e)}")
            return False
