from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# Base Pydantic Models
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class TimestampMixin(BaseModel):
    id: int
    created_at: datetime

# Character Schemas
class CharacterBase(BaseSchema):
    description: str
    system_prompt: str
    is_popular: bool = False
    rank: int
    tag_list: str
    main_image_url: str
    
class CharacterImageBase(BaseSchema):
    character_id: int
    image_url: str
    offset: int
    bounty: int
    is_active: bool = True

class CharacterCreate(CharacterBase):
    pass

class CharacterUpdate(BaseSchema):
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    is_popular: Optional[bool] = None
    rank: Optional[int] = None
    tag_list: Optional[str] = None
    main_image_url: Optional[str] = None

class CharacterImage(CharacterImageBase, TimestampMixin):
    pass

class Character(CharacterBase, TimestampMixin):
    images: List[CharacterImage] = []

class CharacterWithStories(CharacterBase, TimestampMixin):
    stories: List["Story"] = []

# Story Schemas
class StoryBase(BaseSchema):
    character_id: int
    storyline: str
    description: str
    background_image_url: str
    is_active: bool = True

class StoryCreate(StoryBase):
    pass

class StoryUpdate(BaseSchema):
    character_id: Optional[int] = None
    storyline: Optional[str] = None
    description: Optional[str] = None
    background_image_url: Optional[str] = None
    is_active: Optional[bool] = None

class Story(StoryBase, TimestampMixin):
    pass

class StoryWithCharacter(Story):
    character: Character

class StoryWithRelations(Story):
    character: Character
    user_matches: List["StoryUserMatch"] = []

# User Schemas
class UserBase(BaseSchema):
    name: str
    is_active: bool = True

class User(UserBase, TimestampMixin):
    pass

class UserWithProfiles(User):
    profiles: List["Profile"] = []

# Profile Schemas
class ProfileBase(BaseSchema):
    user_id: int
    nickname: str
    thumbnail_url: str

class Profile(ProfileBase, TimestampMixin):
    user: Optional[User] = None

# Story User Match Schemas
class StoryUserMatchBase(BaseSchema):
    story_id: int
    user_id: int
    user_name_in_story: str
    progress: int
    intimacy: int

class StoryUserMatchCreate(StoryUserMatchBase):
    pass

class StoryUserMatch(StoryUserMatchBase, TimestampMixin):
    story: Optional[Story] = None
    user: Optional[User] = None

# Chat History Schemas
class StoryChatHistoryBase(BaseSchema):
    user_id: int
    character_id: int
    story_id: int
    character_image_id: Optional[int] = None
    contents: str
    is_user_message: bool = False
    message_type: str
    is_active: bool = True

class StoryChatHistory(StoryChatHistoryBase, TimestampMixin):
    pass

class StoryChatHistoryWithRelations(StoryChatHistory):
    user: Optional[User] = None
    character: Optional[Character] = None
    story: Optional[Story] = None
    character_image: Optional[CharacterImage] = None

# Chat History Status Schemas
class StoryChatHistoryStatusBase(BaseSchema):
    story_chat_history_id: int
    status: str
    error_message: Optional[str] = None
    elapsed_time: float

class StoryChatHistoryStatus(StoryChatHistoryStatusBase, TimestampMixin):
    pass

# Chat Schemas
class ChatBase(BaseSchema):
    user_id: int
    character_id: int
    title: str
    is_active: bool = True

class Chat(ChatBase, TimestampMixin):
    character: Optional[Character] = None

# Chat Message Schemas
class ChatMessageBase(BaseSchema):
    user_id: int
    content: str
    is_user_message: bool = False

class ChatMessage(ChatMessageBase):
    id: int
    created_at: datetime
    user: Optional[User] = None

# Response Models for API
class CharacterListResponse(BaseSchema):
    characters: List[Character]
    total: int

class StoryListResponse(BaseSchema):
    stories: List[StoryWithCharacter]
    total: int

class CharacterDetailResponse(CharacterWithStories):
    pass

class CharacterProfileResponse(CharacterWithStories):
    images: List[CharacterImage] = []

class StoryDetailResponse(StoryWithRelations):
    pass

# Update forward references
CharacterWithStories.model_rebuild()
StoryWithRelations.model_rebuild()
UserWithProfiles.model_rebuild()
StoryChatHistoryWithRelations.model_rebuild()
