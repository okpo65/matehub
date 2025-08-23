from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import jwt
from app.config import settings
from app.signin.tasks import create_user_account, send_verification_email

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    username: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    username: Optional[str]
    is_verified: bool
    created_at: datetime

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return email
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/")
async def auth_health():
    """Authentication service health check"""
    return {
        "service": "Authentication API",
        "status": "healthy",
        "token_expire_minutes": settings.access_token_expire_minutes
    }

@router.post("/signup")
async def signup(user_data: UserSignup):
    """User registration"""
    try:
        # Submit user creation task to Celery
        task = create_user_account.delay(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            username=user_data.username
        )
        
        return {
            "message": "User registration initiated",
            "task_id": task.id,
            "email": user_data.email
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=TokenResponse)
async def login(user_credentials: UserLogin):
    """User login"""
    # Simulate user authentication (replace with actual database lookup)
    if user_credentials.email == "test@example.com" and user_credentials.password == "password123":
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user_credentials.email}, expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(current_user: str = Depends(verify_token)):
    """User logout"""
    return {"message": f"User {current_user} logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: str = Depends(verify_token)):
    """Get current user information"""
    # Simulate user data retrieval (replace with actual database lookup)
    return UserResponse(
        id="user_123",
        email=current_user,
        full_name="Test User",
        username="testuser",
        is_verified=True,
        created_at=datetime.utcnow()
    )

@router.post("/verify-email")
async def verify_email(email: EmailStr, verification_code: str):
    """Verify user email"""
    # Submit email verification task
    task = send_verification_email.delay(email, verification_code)
    
    return {
        "message": "Email verification initiated",
        "task_id": task.id,
        "email": email
    }

@router.post("/forgot-password")
async def forgot_password(email: EmailStr):
    """Initiate password reset"""
    return {
        "message": f"Password reset instructions sent to {email}",
        "email": email
    }
