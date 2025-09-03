from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.database.models import User
from app.api.jwt_auth import get_current_user_or_anonymous
from app.character.schemas import (
    StoryWithCharacterSchema, 
    StoryDetailResponse, 
    StoryUserMatchSchema,
    StoryUserMatchCreateSchema,
    StoryListResponse
)
from app.database.services import StoryService, RelationshipQueryService
from .schemas import (
    CreateStoryUserMatchRequest,
    StoryUserMatchCreateResponse,
    StoryCreate,
    CharacterCreate
)
from app.database.models import StoryUserMatch as StoryUserMatchModel, Story, User, Character


router = APIRouter(prefix="/stories", tags=["stories"])


@router.get("/", response_model=StoryListResponse)
async def get_stories(
    cursor: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get list of stories with optional filtering"""
    story_service = StoryService(db)
    
    stories = story_service.get_stories(limit, cursor)
    return StoryListResponse(stories=stories, total=len(stories))

@router.get("/popular", response_model=StoryListResponse)
async def get_popular_stories(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    story_service = StoryService(db)
    stories = story_service.get_popular_stories(limit)

    return StoryListResponse(stories=stories, total=len(stories))

@router.get("/{story_id}", response_model=StoryDetailResponse)
async def get_story_detail(
    story_id: int, 
    db: Session = Depends(get_db)
):
    story_service = StoryService(db)
    story = story_service.get_story_detail(story_id)
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return story

@router.get("/character/{character_id}", response_model=List[StoryWithCharacterSchema])
async def get_stories_by_character(
    character_id: int,
    db: Session = Depends(get_db)
):
    """Get all stories for a specific character"""
    story_service = StoryService(db)
    
    try:
        stories = story_service.get_stories_by_character(character_id)
        return stories
    except Exception as e:
        raise HTTPException(status_code=404, detail="Character not found or no stories available")

@router.get("/{story_id}/stats")
async def get_story_stats(
    story_id: int, 
    user_id: int = Depends(get_current_user_or_anonymous), 
    db: Session = Depends(get_db)
):
    """Get engagement statistics for a story"""
    stats_service = RelationshipQueryService(db)
    stats = stats_service.get_story_engagement_stats(story_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return stats

@router.post("/user-match", response_model=StoryUserMatchSchema)
async def create_story_user_match(
    request: CreateStoryUserMatchRequest,
    user_id: int = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    story = db.query(Story).filter(Story.id == request.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Check if match already exists
    existing_match = db.query(StoryUserMatchModel).filter(
        StoryUserMatchModel.story_id == request.story_id,
        StoryUserMatchModel.user_id == user_id
    ).first()
    
    if existing_match:
        raise HTTPException(status_code=400, detail="Story user match already exists")
    
    # Create new match
    story_user_match = StoryUserMatchModel(
        story_id=request.story_id,
        user_id=user_id,
        user_name_in_story=request.user_name_in_story,
        progress=request.progress or 0,
        intimacy=request.intimacy or 0
    )
    
    db.add(story_user_match)
    db.commit()
    db.refresh(story_user_match)
    
    return StoryUserMatchCreateResponse(
        id=story_user_match.id,
        story_id=story_user_match.story_id,
        user_name_in_story=story_user_match.user_name_in_story,
        progress=story_user_match.progress,
        intimacy=story_user_match.intimacy,
        message="Story user match created successfully"
    )

@router.get("/user-match/", response_model=List[StoryWithCharacterSchema])
async def get_user_story_matches(
    user_id: int = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Get all story matches for a specific user"""
    story_service = StoryService(db)

    try:
        stories = story_service.get_user_story_matches(user_id)
        return stories
    except Exception as e:
        raise HTTPException(status_code=404, detail="User not found or no story matches")

@router.put("/user-match/{match_id}/progress")
async def update_story_progress(
    match_id: int,
    progress: int = Query(..., ge=0),
    intimacy: Optional[int] = Query(None, ge=0),
    user_id: int = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):    
    match = db.query(StoryUserMatchModel).filter(StoryUserMatchModel.id == match_id).first()
    
    if not match:
        raise HTTPException(status_code=404, detail="Story user match not found")
    
    match.progress = progress
    if intimacy is not None:
        match.intimacy = intimacy
    
    db.commit()
    db.refresh(match)
    
    return {
        "message": "Progress updated successfully",
        "match_id": match_id,
        "progress": match.progress,
        "intimacy": match.intimacy
    }


@router.post("/create")
async def create_story(
    story_data: StoryCreate,
    user_id: int = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    story = Story(
        character_id=story_data.character_id,
        storyline=story_data.storyline,
        description=story_data.description,
        background_image_url=story_data.background_image_url,
    )

    db.add(story)
    db.commit()
    db.refresh(story)

    return story

@router.post("/character/create")
async def create_character(
    character_data: CharacterCreate,
    user_id: int = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    character = Character(
        name=character_data.name,
        description=character_data.description,
        system_prompt=character_data.system_prompt,
        tag_list=character_data.tag_list,
        main_image_url=character_data.main_image_url
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    return character