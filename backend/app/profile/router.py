from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.signin.router import verify_token
from app.profile.tasks import update_user_profile, upload_profile_image, generate_user_stats

router = APIRouter(prefix="/profile", tags=["Profile"])

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None

class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    username: str
    bio: Optional[str]
    location: Optional[str]
    website: Optional[str]
    phone: Optional[str]
    profile_image_url: Optional[str]
    is_verified: bool
    created_at: datetime
    updated_at: datetime

class UserStats(BaseModel):
    total_logins: int
    last_login: datetime
    profile_views: int
    account_age_days: int

@router.get("/")
async def profile_health():
    """Profile service health check"""
    return {
        "service": "Profile API",
        "status": "healthy"
    }

@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(current_user: str = Depends(verify_token)):
    """Get current user's profile"""
    # Simulate profile data retrieval (replace with actual database lookup)
    return ProfileResponse(
        id="user_123",
        email=current_user,
        full_name="Test User",
        username="testuser",
        bio="I'm a software developer passionate about AI and web technologies.",
        location="San Francisco, CA",
        website="https://example.com",
        phone="+1-555-0123",
        profile_image_url="https://example.com/avatar.jpg",
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@router.put("/me")
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: str = Depends(verify_token)
):
    """Update current user's profile"""
    try:
        # Submit profile update task to Celery
        task = update_user_profile.delay(
            user_email=current_user,
            profile_data=profile_data.dict(exclude_unset=True)
        )
        
        return {
            "message": "Profile update initiated",
            "task_id": task.id,
            "user": current_user
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Profile update failed: {str(e)}")

@router.post("/upload-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: str = Depends(verify_token)
):
    """Upload profile image"""
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        file_content = await file.read()
        
        # Submit image upload task to Celery
        task = upload_profile_image.delay(
            user_email=current_user,
            filename=file.filename,
            file_size=len(file_content),
            content_type=file.content_type
        )
        
        return {
            "message": "Profile image upload initiated",
            "task_id": task.id,
            "filename": file.filename,
            "size": len(file_content)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image upload failed: {str(e)}")

@router.get("/stats", response_model=UserStats)
async def get_user_stats(current_user: str = Depends(verify_token)):
    """Get user statistics"""
    try:
        # Submit stats generation task to Celery
        task = generate_user_stats.delay(current_user)
        
        # For demo purposes, return mock data immediately
        # In production, you'd return the task ID and have a separate endpoint to get results
        return UserStats(
            total_logins=42,
            last_login=datetime.utcnow(),
            profile_views=156,
            account_age_days=30
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user stats: {str(e)}")

@router.get("/{user_id}", response_model=ProfileResponse)
async def get_user_profile(user_id: str):
    """Get public profile of any user"""
    # Simulate public profile retrieval
    return ProfileResponse(
        id=user_id,
        email="public@example.com",
        full_name="Public User",
        username="publicuser",
        bio="This is a public profile.",
        location="New York, NY",
        website="https://publicuser.com",
        phone=None,  # Private information not shown
        profile_image_url="https://example.com/public-avatar.jpg",
        is_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@router.get("/search/{query}")
async def search_profiles(query: str, limit: int = 10):
    """Search user profiles"""
    # Simulate profile search
    return {
        "query": query,
        "results": [
            {
                "id": "user_1",
                "username": "john_doe",
                "full_name": "John Doe",
                "bio": "Software engineer",
                "profile_image_url": "https://example.com/john.jpg"
            },
            {
                "id": "user_2", 
                "username": "jane_smith",
                "full_name": "Jane Smith",
                "bio": "Product manager",
                "profile_image_url": "https://example.com/jane.jpg"
            }
        ],
        "total": 2,
        "limit": limit
    }
