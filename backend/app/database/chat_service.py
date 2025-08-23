from calendar import c
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.database.models import StoryChatHistory, User, ChatMessage, Character, StoryChatHistoryStatus
from app.database.connection import get_db_session
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db or get_db_session()
        self._should_close = db is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.db.close()
    
    def get_or_create_user(self, user_id: int) -> User:
        """Get existing user or create new one"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                user = User(
                    id=user_id,
                    name=f"User_{user_id}",  # Provide default name
                    is_active=True
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
                logger.info(f"Created new user: {user_id}")
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error getting/creating user {user_id}: {e}")
            raise

    def get_character(self, character_id: int) -> Optional[Character]:
        try:
            return self.db.query(Character).filter(Character.id == character_id).first()
        except Exception as e:
            logger.error(f"Error getting character {character_id}: {e}")
            return None
    
    def get_user_chat_history(self, user_id: int, story_id: int, max_count: int = 10) -> List[StoryChatHistory]:
        """Get chat history for a user and story"""
        try:
            query = self.db.query(StoryChatHistory).filter(
                StoryChatHistory.user_id == user_id, 
                StoryChatHistory.story_id == story_id,
                StoryChatHistory.is_active == True
            )
            messages = query.order_by(StoryChatHistory.created_at.desc()).limit(max_count).all()
            
            return messages
        except Exception as e:
            logger.error(f"Error getting chat history for user {user_id}: {e}")
            return []
    
    def add_message(self, user_id: int, character_id: int, story_id: int, message: str, character_image_id: int = None, message_type: str = "text", is_user_message: bool = True) -> Optional[StoryChatHistory]:
        """Add a message to the chat history"""
        try:
            # Ensure user exists
            self.get_or_create_user(user_id)
            
            # Create message record
            chat_message = StoryChatHistory(
                user_id=user_id,
                character_id=character_id,
                story_id=story_id,
                character_image_id=character_image_id,
                contents=message,
                message_type=message_type,
                is_user_message=is_user_message,
                is_active=True
            )
            
            self.db.add(chat_message)
            self.db.commit()
            self.db.refresh(chat_message)
            
            logger.info(f"Added message for user {user_id}, story {story_id}")
            return chat_message
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding message for user {user_id}: {e}")
            return None

    def add_story_chat_history_status(self, story_chat_history_id: int, status: str, error_message: str = None, elapsed_time: float = 0) -> Optional[StoryChatHistoryStatus]:
        """Add a status to a chat history"""
        try:
            status = StoryChatHistoryStatus(
                story_chat_history_id=story_chat_history_id,
                status=status,
                error_message=error_message,
                elapsed_time=elapsed_time
            )
            self.db.add(status)
            self.db.commit()
            return status
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding status for story chat history {story_chat_history_id}: {e}")
            return None

    def get_story_chat_history_status(self, story_chat_history_id: int) -> Optional[StoryChatHistoryStatus]:

        stmt = (
            select(StoryChatHistoryStatus)
            .where(StoryChatHistoryStatus.story_chat_history_id == story_chat_history_id)
            .order_by(StoryChatHistoryStatus.created_at.desc())
            .limit(1)
        )
        latest = self.db.execute(stmt).scalars().first()
        return latest
    
    def get_story_chat_history_by_id(self, story_chat_history_id: int) -> Optional[StoryChatHistory]:
        """Get a chat history by ID"""
        try:
            return self.db.query(StoryChatHistory).filter(StoryChatHistory.id == story_chat_history_id).first()
        except Exception as e:
            logger.error(f"Error getting chat history {story_chat_history_id}: {e}")
            return None

    def update_story_chat_history(self, story_chat_history_id: int, contents: str) -> Optional[StoryChatHistory]:
        """Update the contents of a chat history"""
        try:
            story_chat_history = self.db.query(StoryChatHistory).filter(StoryChatHistory.id == story_chat_history_id).first()
            story_chat_history.contents = contents
            self.db.commit()
            return story_chat_history
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating chat history {story_chat_history_id}: {e}")
            return None
