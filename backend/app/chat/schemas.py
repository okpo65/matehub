from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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
    limit: int

class ChatHistoryRequest(BaseModel):
    user_id: int
    story_id: int
    limit: int = 20
    cursor: Optional[int] = None
    direction: str = "before"
