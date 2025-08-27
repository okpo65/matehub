from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.database.schemas import BaseSchema, TimestampMixin
from app.character.schemas import CharacterBaseSchema

class ChatHistoryResponse(BaseModel):
    id: int
    user_id: int
    character_id: int
    story_id: int
    character_image_id: Optional[int]
    contents: str
    is_user_message: bool
    message_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class CursorPaginatedChatHistoryResponse(BaseModel):
    messages: List[ChatHistoryResponse]
    has_more: bool
    next_cursor: Optional[int]
    total_count: int

class ChatHistoryRequest(BaseModel):
    user_id: int
    story_id: int
    limit: int = 20
    cursor: Optional[int] = None
    direction: str = "before"

class ChatSendRequest(BaseModel):
    story_id: int
    character_id: int
    character_image_id: Optional[int] = None
    message: str

class ChatSendResponse(BaseModel):
    user_message_id: int
    ai_message_id: int
    ai_response: str
    success: bool

# Chat Schemas
class ChatBaseSchema(BaseSchema):
    user_id: int
    character_id: int
    title: str
    is_active: bool = True

class ChatSchema(ChatBaseSchema, TimestampMixin):
    character: Optional[CharacterBaseSchema] = None
