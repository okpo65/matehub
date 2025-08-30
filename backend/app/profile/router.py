from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.config import settings
from app.api.jwt_auth import get_current_user_required
from app.profile.services import ProfileService
from app.profile.schemas import ProfileResponse
from app.profile.services import UserService
from app.database.connection import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/")
async def get_profile(
    user_id: int = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    return ProfileService(db).get_profile(user_id)

@router.put("/", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileResponse,
    user_id: int = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    return ProfileService(db).update_profile(user_id, profile_data)