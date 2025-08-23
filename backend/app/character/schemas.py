from tkinter import Image
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class CharacterResponse(BaseModel):
    id: int
    description: str
    is_popular: bool
    rank: int
    tag_list: str
    created_at: datetime

    class Config:
        from_attributes = True

class CharacterPhotoResponse(BaseModel):
    id: int
    character_id: int
    image_url: str
    offset: int
    bounty: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CharacterDetailResponse(BaseModel):
    id: int
    description: str
    system_prompt: str
    storyline: str
    story_id: int
    is_popular: bool
    rank: int
    tag_list: str
    created_at: datetime
    main_image_url: str
    images: List[CharacterPhotoResponse]

    class Config:
        from_attributes = True
