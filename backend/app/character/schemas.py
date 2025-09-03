from tkinter import Image
from pydantic import BaseModel, ConfigDict
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
        
# Base Pydantic Models
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class TimestampMixin(BaseModel):
    id: int
    created_at: datetime

# Character Schemas
class CharacterBaseSchema(BaseSchema):
    name: str
    description: str
    system_prompt: str
    tag_list: str
    main_image_url: str
    
class CharacterImageBaseSchema(BaseSchema):
    character_id: int
    image_url: str
    offset: int
    bounty: int
    is_active: bool = True

class CharacterCreateSchema(CharacterBaseSchema):
    pass

class CharacterUpdateDBSchema(BaseSchema):
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    is_popular: Optional[bool] = None
    rank: Optional[int] = None
    tag_list: Optional[str] = None
    main_image_url: Optional[str] = None

class CharacterImageSchema(CharacterImageBaseSchema, TimestampMixin):
    pass

class CharacterWithImagesSchema(CharacterBaseSchema, TimestampMixin):
    images: List[CharacterImageBaseSchema] = []

class CharacterWithStoriesSchema(CharacterBaseSchema, TimestampMixin):
    stories: List["StoryBaseSchema"] = []

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

# User Schemas
class UserBaseSchema(BaseSchema):
    name: str
    is_active: bool = True

class UserSchema(UserBaseSchema, TimestampMixin):
    pass

class UserWithProfilesSchema(UserBaseSchema, TimestampMixin):
    profiles: List["ProfileBaseSchema"] = []

# Profile Schemas
class ProfileBaseSchema(BaseSchema):
    user_id: int
    nickname: str
    thumbnail_url: str

class ProfileSchema(ProfileBaseSchema, TimestampMixin):
    user: Optional[UserBaseSchema] = None

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

# Chat Schemas
class ChatDBBase(BaseSchema):
    user_id: int
    character_id: int
    title: str
    is_active: bool = True

class ChatSchema(ChatDBBase, TimestampMixin):
    character: Optional[CharacterBaseSchema] = None

# Chat Message Schemas
class ChatMessageDBBase(BaseSchema):
    user_id: int
    content: str
    is_user_message: bool = False

class ChatMessageDB(ChatMessageDBBase, TimestampMixin):
    pass

# Response Models for API
class CharacterListResponse(BaseSchema):
    characters: List[CharacterBaseSchema]
    total: int

class StoryListResponse(BaseSchema):
    stories: List[StoryWithCharacterSchema]
    total: int

class CharacterDetailResponse(CharacterWithStoriesSchema):
    pass

class CharacterProfileResponse(CharacterWithStoriesSchema):
    images: List[CharacterImageBaseSchema] = []

class StoryDetailResponse(StoryWithRelationsSchema):
    pass

# Update forward references
CharacterWithStoriesSchema.model_rebuild()
StoryWithRelationsSchema.model_rebuild()
UserWithProfilesSchema.model_rebuild()
StoryChatHistoryWithRelationsSchema.model_rebuild()
