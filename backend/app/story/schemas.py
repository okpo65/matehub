from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.character.schemas import CharacterBaseSchema, StoryUserMatchBaseSchema, CharacterImageBaseSchema
from app.database.schemas import BaseSchema, TimestampMixin
from app.profile.schemas import UserBaseSchema


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
    progress: int
    intimacy: int
    created_at: datetime

    class Config:
        from_attributes = True

class CreateStoryUserMatchRequest(BaseModel):
    story_id: int
    user_name_in_story: Optional[str] = None
    progress: Optional[int] = 0
    intimacy: Optional[int] = 0

class StoryUserMatchCreateResponse(BaseModel):
    id: int
    story_id: int
    user_name_in_story: str
    progress: int
    intimacy: int
    message: str

    class Config:
        from_attributes = True

# Story Schemas
class StoryBaseSchema(BaseSchema):
    character_id: int
    storyline: str
    description: str
    background_image_url: str
    is_active: bool = True

class StoryCreateSchema(StoryBaseSchema):
    pass

class StoryUpdateSchema(BaseSchema):
    character_id: Optional[int] = None
    storyline: Optional[str] = None
    description: Optional[str] = None
    background_image_url: Optional[str] = None
    is_active: Optional[bool] = None

class StorySchema(StoryBaseSchema, TimestampMixin):
    pass

class StoryWithCharacterSchema(StoryBaseSchema, TimestampMixin):
    character: CharacterBaseSchema

class StoryWithRelationsSchema(StoryBaseSchema, TimestampMixin):
    character: CharacterBaseSchema
    user_matches: List["StoryUserMatchBaseSchema"] = []

# Story User Match Schemas
class StoryUserMatchBaseSchema(BaseSchema):
    story_id: int
    user_id: int
    user_name_in_story: str
    progress: int
    intimacy: int

class StoryUserMatchCreateSchema(StoryUserMatchBaseSchema):
    pass

class StoryUserMatchSchema(StoryUserMatchBaseSchema, TimestampMixin):
    story: Optional[StoryBaseSchema] = None
    user: Optional[UserBaseSchema] = None

# Chat History Schemas
class StoryChatHistoryBaseSchema(BaseSchema):
    user_id: int
    character_id: int
    story_id: int
    character_image_id: Optional[int] = None
    contents: str
    is_user_message: bool = False
    message_type: str
    is_active: bool = True

class StoryChatHistorySchema(StoryChatHistoryBaseSchema, TimestampMixin):
    pass

class StoryChatHistoryWithRelationsSchema(StoryChatHistoryBaseSchema, TimestampMixin):
    user: Optional[UserBaseSchema] = None
    character: Optional[CharacterBaseSchema] = None
    story: Optional[StoryBaseSchema] = None
    character_image: Optional[CharacterImageBaseSchema] = None

# Chat History Status Schemas
class StoryChatHistoryStatusBaseSchema(BaseSchema):
    story_chat_history_id: int
    status: str
    error_message: Optional[str] = None
    elapsed_time: float

class StoryChatHistoryStatusSchema(StoryChatHistoryStatusBaseSchema, TimestampMixin):
    pass


class StoryListResponse(BaseSchema):
    stories: List[StoryWithCharacterSchema]
    total: int

class StoryDetailResponse(StoryWithRelationsSchema):
    pass

class StoryCreate(BaseModel):
    character_id: int
    storyline: str
    description: str
    background_image_url: str = ""

class CharacterCreate(BaseModel):   
    name: str
    description: str
    system_prompt: str
    tag_list: str = ""
    main_image_url: str = ""

StoryChatHistoryWithRelationsSchema.model_rebuild()