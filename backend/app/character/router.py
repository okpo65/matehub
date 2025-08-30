from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.database.models import User
from app.api.jwt_auth import get_current_user_or_anonymous
from app.character.schemas import CharacterDetailResponse, CharacterImageSchema, CharacterWithStoriesSchema, CharacterProfileResponse
from app.database.services import CharacterService



router = APIRouter(prefix="/characters", tags=["characters"])

@router.get("/", response_model=List[CharacterWithStoriesSchema])
async def get_characters(
    db: Session = Depends(get_db)
):
    return CharacterService(db).get_characters()

@router.get("/story_detail/{character_id}", response_model=CharacterDetailResponse)
async def get_character_detail(
    character_id: int, 
    user_id: int = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    return CharacterService(db).get_character_story_detail(character_id)

@router.get("/{character_id}/photos", response_model=List[CharacterImageSchema])
async def get_character_photos(
    character_id: int,
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    return CharacterService(db).get_character_photos(character_id, active_only)

@router.get("/profile/{character_id}", response_model=CharacterProfileResponse)
async def get_character_profile(character_id: int, db: Session = Depends(get_db)):
    return CharacterService(db).get_character_profile(character_id)

@router.get("/popular", response_model=List[CharacterWithStoriesSchema])
async def get_popular_characters(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    return CharacterService(db).get_popular_characters(limit)
