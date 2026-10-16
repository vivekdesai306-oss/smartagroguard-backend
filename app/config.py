import os
from dotenv import load_dotenv

# Load env file from the project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

class Settings:
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "agroguard")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "supersecretkey_change_me_in_production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    GROWTH_STAGE_MODEL_PATH: str = os.getenv("GROWTH_STAGE_MODEL_PATH", "app/ml_models/growth_stage_model.pt")
    DISEASE_MODEL_PATH: str = os.getenv("DISEASE_MODEL_PATH", "app/ml_models/disease_model.pt")
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"

    # Cloudinary image storage (set all three to enable cloud uploads)
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    USE_CLOUDINARY: bool = bool(
        os.getenv("CLOUDINARY_CLOUD_NAME") and
        os.getenv("CLOUDINARY_API_KEY") and
        os.getenv("CLOUDINARY_API_SECRET")
    )

    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

    # Module 4: Temporal Analytics Configuration
    MODULE4_TIMEZONE: str = os.getenv("MODULE4_TIMEZONE", "Asia/Kolkata")
    MODULE4_HEIGHT_TOLERANCE_CM: float = float(os.getenv("MODULE4_HEIGHT_TOLERANCE_CM", "2.0"))
    MODULE4_MIN_DISEASE_CONFIDENCE: float = float(os.getenv("MODULE4_MIN_DISEASE_CONFIDENCE", "0.75"))
    MODULE4_MIN_PERSISTENCE_COUNT: int = int(os.getenv("MODULE4_MIN_PERSISTENCE_COUNT", "2"))
    MODULE4_MIN_RECOVERY_COUNT: int = int(os.getenv("MODULE4_MIN_RECOVERY_COUNT", "2"))
    MODULE4_TIMELINE_MAX_PAGE_SIZE: int = int(os.getenv("MODULE4_TIMELINE_MAX_PAGE_SIZE", "100"))
    MODULE4_TIMELINE_DEFAULT_PAGE_SIZE: int = int(os.getenv("MODULE4_TIMELINE_DEFAULT_PAGE_SIZE", "20"))
    MODULE4_NO_DISEASE_LABELS: str = os.getenv(
        "MODULE4_NO_DISEASE_LABELS",
        "Healthy,HEALTHY,NO_DISEASE,UNKNOWN"
    )

settings = Settings()

# Ensure uploads directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
