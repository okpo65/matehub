from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import Optional
from app.database.connection import get_db
from app.database.models import StoryChatHistory, User, Story
from .schemas import CursorPaginatedChatHistoryResponse, ChatHistoryResponse

router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/history", response_model=CursorPaginatedChatHistoryResponse)
async def get_chat_history(
    user_id: int = Query(..., description="User ID"),
    story_id: int = Query(..., description="Story ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of messages to fetch"),
    cursor: Optional[int] = Query(None, description="Message ID cursor for pagination"),
    db: Session = Depends(get_db)
):

    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify story exists
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Build base query
    messages = db.query(StoryChatHistory).filter(
        StoryChatHistory.user_id == user_id,
        StoryChatHistory.story_id == story_id,
        StoryChatHistory.is_active == True,
        StoryChatHistory.id < cursor if cursor else True
    ).order_by(StoryChatHistory.id).all()[-limit:]

    has_more = len(messages) == limit
    
    next_cursor = messages[0].id if has_more else None
    
    message_responses = [
        ChatHistoryResponse(
            id=msg.id,
            user_id=msg.user_id,
            character_id=msg.character_id,
            story_id=msg.story_id,
            character_image_id=msg.character_image_id,
            contents=msg.contents,
            is_user_message=msg.is_user_message,
            message_type=msg.message_type,
            created_at=msg.created_at
        ) for msg in messages
    ]
    
    return CursorPaginatedChatHistoryResponse(
        messages=message_responses,
        has_more=has_more,
        next_cursor=next_cursor,
        limit=limit
    )