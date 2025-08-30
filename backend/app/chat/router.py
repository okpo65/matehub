from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import Optional
from app.database.connection import get_db
from app.database.models import StoryChatHistory, User, Story
from app.api.jwt_auth import get_current_user_or_anonymous
from .schemas import CursorPaginatedChatHistoryResponse, ChatHistoryResponse, ChatSendRequest, ChatSendResponse
from app.profile.services import UserService
router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/history", response_model=CursorPaginatedChatHistoryResponse)
async def get_chat_history(
    story_id: int = Query(..., description="Story ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of messages to fetch"),
    cursor: Optional[int] = Query(None, description="Message ID cursor for pagination"),
    user_id: int = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    query = db.query(StoryChatHistory).filter(
        and_(
            StoryChatHistory.user_id == user_id,
            StoryChatHistory.story_id == story_id,
            StoryChatHistory.is_active == True
        )
    )
    
    # Apply cursor pagination if provided
    if cursor:
        query = query.filter(StoryChatHistory.id < cursor)
    
    # Order by ID descending and limit
    messages = query.order_by(desc(StoryChatHistory.id)).limit(limit + 1).all()
    
    # Check if there are more messages
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:-1]
    
    # Get next cursor
    next_cursor = messages[-1].id if messages and has_more else None
    
    # Convert to response format
    chat_messages = []
    for msg in reversed(messages):  # Reverse to show oldest first
        chat_messages.append(ChatHistoryResponse(
            id=msg.id,
            user_id=msg.user_id,
            character_id=msg.character_id,
            story_id=msg.story_id,
            character_image_id=msg.character_image_id,
            contents=msg.contents,
            is_user_message=msg.is_user_message,
            message_type=msg.message_type,
            created_at=msg.created_at
        ))
    
    return CursorPaginatedChatHistoryResponse(
        messages=chat_messages,
        has_more=has_more,
        next_cursor=next_cursor,
        total_count=len(chat_messages)
    )

@router.post("/send", response_model=ChatSendResponse)
async def send_chat_message(
    chat_request: ChatSendRequest,
    user_id: int = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Send chat message (works for both authenticated and anonymous users)"""
    
    # Verify story exists
    story = db.query(Story).filter(Story.id == chat_request.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    try:
        # Create user message
        user_message = StoryChatHistory(
            user_id=user_id,
            character_id=chat_request.character_id,
            story_id=chat_request.story_id,
            character_image_id=chat_request.character_image_id,
            contents=chat_request.message,
            is_user_message=True,
            message_type="text"
        )
        
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # TODO: Add AI response generation here
        # For now, return a simple response
        ai_response = f"AI response to: {chat_request.message}"
        
        ai_message = StoryChatHistory(
            user_id=user_id,
            character_id=chat_request.character_id,
            story_id=chat_request.story_id,
            character_image_id=chat_request.character_image_id,
            contents=ai_response,
            is_user_message=False,
            message_type="text"
        )
        
        db.add(ai_message)
        db.commit()
        db.refresh(ai_message)
        
        return ChatSendResponse(
            user_message_id=user_message.id,
            ai_message_id=ai_message.id,
            ai_response=ai_response,
            success=True
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")