from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class StoryResponse(BaseModel):
    id: int
    character_id: int
    storyline: str
    description: str
    background_image_url: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class StoryDetailResponse(BaseModel):
    id: int
    character_id: int
    storyline: str
    description: str
    background_image_url: str
    is_active: bool
    created_at: datetime
    character_name: Optional[str] = None

    class Config:
        from_attributes = True

class StoryUserMatchResponse(BaseModel):
    id: int
    story_id: int
    user_id: int
    progress: int
    intimacy: int
    created_at: datetime

    class Config:
        from_attributes = True

class CreateStoryUserMatchRequest(BaseModel):
    story_id: int
    user_id: int
    user_name_in_story: Optional[str] = None
    progress: Optional[int] = 0
    intimacy: Optional[int] = 0

class StoryUserMatchCreateResponse(BaseModel):
    id: int
    story_id: int
    user_id: int
    progress: int
    intimacy: int
    message: str

    class Config:
        from_attributes = True
