import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

from .config import settings
from .database import Database
from .services.inference_service import InferenceService
from .routers import auth, farms, scans, suitability, advisory, history, weather, dosage, irrigation, reminders, harvest, lifecycle

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agroguard.main")

app = FastAPI(
    title="Smart AgroGuard Backend",
    description="Python FastAPI Backend for Smart AgroGuard Precision Agriculture Platform (Modules 1 to 6)",
    version="2.0.0"
)

# Alias to support both `uvicorn app.main:app` and `uvicorn app.main:main`
main = app

# Enable CORS for frontend connectivity (Expo client etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, required for mobile dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploads directory statically to render captured images in frontend
uploads_dir = settings.UPLOAD_DIR
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database connection...")
    Database.connect_db()
    
    logger.info("Pre-loading PyTorch models...")
    InferenceService.load_models()
    logger.info("Startup sequence complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Closing database connection...")
    Database.close_db()
    logger.info("Shutdown sequence complete.")

# Include Routers
app.include_router(auth.router)
app.include_router(farms.router)
app.include_router(scans.router)
app.include_router(suitability.router)
app.include_router(advisory.router)
app.include_router(history.router)
app.include_router(weather.router)
app.include_router(dosage.router)
app.include_router(irrigation.router)
app.include_router(reminders.router)
app.include_router(harvest.router)
app.include_router(lifecycle.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Smart AgroGuard Module 2 Backend API",
        "models_loaded": {
            "growth_stage_model": InferenceService.growth_model is not None,
            "disease_model": InferenceService.disease_model is not None
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

