from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.database.schemas import (
    StoryWithCharacter, 
    StoryDetailResponse, 
    StoryUserMatch,
    StoryUserMatchCreate,
    StoryListResponse
)
from app.database.services import StoryService, RelationshipQueryService
from .schemas import (
    CreateStoryUserMatchRequest,
    StoryUserMatchCreateResponse
)

router = APIRouter(prefix="/stories", tags=["stories"])

@router.get("/", response_model=StoryListResponse)
async def get_stories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    character_id: Optional[int] = None,
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get list of stories with optional filtering"""
    story_service = StoryService(db)
    
    if character_id:
        # Get stories by specific character
        stories = story_service.get_stories_by_character(character_id)
        # Apply pagination manually since service doesn't support it yet
        paginated_stories = stories[skip:skip + limit]
        return StoryListResponse(stories=paginated_stories, total=len(stories))
    else:
        # For now, get all stories and paginate manually
        # TODO: Add pagination support to service layer
        all_stories = []
        # This is a placeholder - you might want to add a get_all_stories method
        return StoryListResponse(stories=all_stories[skip:skip + limit], total=len(all_stories))

@router.get("/{story_id}", response_model=StoryDetailResponse)
async def get_story_detail(story_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific story"""
    story_service = StoryService(db)
    story = story_service.get_story_detail(story_id)
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return story

@router.get("/character/{character_id}", response_model=List[StoryWithCharacter])
async def get_stories_by_character(
    character_id: int,
    active_only: bool = Query(True),
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
async def get_story_stats(story_id: int, db: Session = Depends(get_db)):
    """Get engagement statistics for a story"""
    stats_service = RelationshipQueryService(db)
    stats = stats_service.get_story_engagement_stats(story_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return stats

@router.post("/user-match", response_model=StoryUserMatchCreateResponse)
async def create_story_user_match(
    request: CreateStoryUserMatchRequest,
    db: Session = Depends(get_db)
):
    """Create a new story user match"""
    from app.database.models import StoryUserMatch as StoryUserMatchModel, Story, User
    
    # Verify story exists
    story = db.query(Story).filter(Story.id == request.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Verify user exists
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if match already exists
    existing_match = db.query(StoryUserMatchModel).filter(
        StoryUserMatchModel.story_id == request.story_id,
        StoryUserMatchModel.user_id == request.user_id
    ).first()
    
    if existing_match:
        raise HTTPException(status_code=400, detail="Story user match already exists")
    
    # Create new match
    story_user_match = StoryUserMatchModel(
        story_id=request.story_id,
        user_id=request.user_id,
        user_name_in_story=request.user_name_in_story or user.name,
        progress=request.progress or 0,
        intimacy=request.intimacy or 0
    )
    
    db.add(story_user_match)
    db.commit()
    db.refresh(story_user_match)
    
    return StoryUserMatchCreateResponse(
        id=story_user_match.id,
        story_id=story_user_match.story_id,
        user_id=story_user_match.user_id,
        progress=story_user_match.progress,
        intimacy=story_user_match.intimacy,
        message="Story user match created successfully"
    )

@router.get("/user-match/{user_id}", response_model=List[StoryWithCharacter])
async def get_user_story_matches(
    user_id: int,
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
    db: Session = Depends(get_db)
):
    """Update progress and optionally intimacy for a story user match"""
    from app.database.models import StoryUserMatch as StoryUserMatchModel
    
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
