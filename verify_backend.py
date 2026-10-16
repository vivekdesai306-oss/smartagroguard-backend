import sys

print("--- AgroGuard Backend Verification Utility ---")

try:
    print("Testing configuration import...")
    from app.config import settings
    print("[SUCCESS] Config loaded successfully.")
    print(f"  Upload Dir: {settings.UPLOAD_DIR}")
    print(f"  Database Name: {settings.DATABASE_NAME}")
    
    print("\nTesting database module import...")
    from app.database import get_database
    print("[SUCCESS] Database module loaded successfully.")
    
    print("\nTesting schemas import...")
    from app.schemas import UserRegister, FarmCreate, ScanOut
    print("[SUCCESS] Schemas loaded successfully.")
    
    print("\nTesting CV Service import...")
    from app.services.cv_service import CVService
    print("[SUCCESS] CV Service loaded successfully.")
    
    print("\nTesting Inference Service import...")
    from app.services.inference_service import InferenceService
    InferenceService.load_models()
    print("[SUCCESS] Inference Service loaded successfully (running checks/fallback).")
    
    print("\nTesting Auth Service import...")
    from app.services.auth_service import AuthService
    print("[SUCCESS] Auth Service loaded successfully.")
    
    print("\nTesting App Main import...")
    from app.main import app
    print("[SUCCESS] FastAPI app initialized successfully with all registered routes.")
    
    print("\n==============================================")
    print("Backend check complete. No import or syntax errors found!")
    print("==============================================")
    
except Exception as e:
    print(f"\n[ERROR] Error during verification: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
