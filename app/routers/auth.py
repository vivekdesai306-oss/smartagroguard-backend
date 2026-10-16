import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, EmailStr

from ..database import get_database
from ..schemas import UserRegister, UserOut, Token, UserLogin
from ..services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

def generate_short_id(prefix: str) -> str:
    # Prefix (1 char) + '_' (1 char) + 8 hex chars = 10 chars, perfect for Varchar(10)
    random_hex = secrets.token_hex(4) # 8 characters
    return f"{prefix}_{random_hex}"

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncIOMotorDatabase = Depends(get_database)):
    # Check if user already exists
    existing_user = await db["users"].find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered."
        )

    # Hash the password
    hashed_password = AuthService.get_password_hash(user_data.password)
    
    # Generate uid (e.g. u_abcdef12)
    uid = generate_short_id("u")

    new_user = {
        "uid": uid,
        "user_name": user_data.user_name,
        "user_role": user_data.user_role,
        "password": hashed_password,
        "email": user_data.email,
        "mobile_no": user_data.mobile_no
    }

    await db["users"].insert_one(new_user)
    return new_user

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: AsyncIOMotorDatabase = Depends(get_database)):
    user = await db["users"].find_one({"email": user_credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not AuthService.verify_password(user_credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Generate token
    access_token = AuthService.create_access_token(
        data={"email": user["email"], "uid": user["uid"], "role": user["user_role"]}
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def get_current_user_profile(
    current_user: dict = Depends(AuthService.get_current_user)
):
    """
    Retrieve authenticated farmer profile.
    """
    return current_user

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    # Find user by email
    user = await db["users"].find_one({"email": request.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A user with this email address was not found."
        )

    # Hash the new password using the direct bcrypt service
    hashed_password = AuthService.get_password_hash(request.new_password)
    
    # Update password in MongoDB
    await db["users"].update_one(
        {"email": request.email},
        {"$set": {"password": hashed_password}}
    )
    
    return {"message": "Password updated successfully!"}
