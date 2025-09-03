from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional
from datetime import datetime
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(BaseModel):
    __tablename__ = "users"
    
    is_active = Column(Boolean, default=True)
    # Authentication fields - Kakao only
    anonymous_user_id = Column(String(36), nullable=True, unique=True)  # UUID for anonymous users
    kakao_id = Column(String(255), nullable=True, unique=True)  # Kakao user ID
    is_anonymous = Column(Boolean, default=True)
    
    # OAuth tokens
    kakao_access_token = Column(Text, nullable=True)  # Kakao access token
    kakao_refresh_token = Column(Text, nullable=True)  # Kakao refresh token
    kakao_token_expires_at = Column(DateTime(timezone=True), nullable=True)  # Token expiration time
    
    # JWT refresh token
    refresh_token = Column(Text, nullable=True)  # JWT refresh token
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    profiles = relationship("Profile", back_populates="user", cascade="all, delete-orphan")
    story_matches = relationship("StoryUserMatch", back_populates="user", cascade="all, delete-orphan")
    chat_histories = relationship("StoryChatHistory", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

class UserSession(BaseModel):
    __tablename__ = "user_sessions"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(36), nullable=False, unique=True)  # UUID for session
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")

class Profile(BaseModel):
    __tablename__ = "profiles"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nickname = Column(String(255), nullable=False)
    tag_name = Column(String(255), nullable=False)
    thumbnail_url = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    # Relationships
    user = relationship("User", back_populates="profiles")

class Story(BaseModel):
    __tablename__ = "stories"
    
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    storyline = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    background_image_url = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_popular = Column(Boolean, default=False)
    rank = Column(Integer, nullable=False)

    # Relationships
    character = relationship("Character", back_populates="stories")
    user_matches = relationship("StoryUserMatch", back_populates="story", cascade="all, delete-orphan")
    chat_histories = relationship("StoryChatHistory", back_populates="story", cascade="all, delete-orphan")

class Character(BaseModel):
    __tablename__ = "characters"
    
    description = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=False)
    tag_list = Column(String(255), nullable=False)
    main_image_url = Column(String(255), nullable=False)

    # Relationships
    stories = relationship("Story", back_populates="character", cascade="all, delete-orphan")
    images = relationship("CharacterImage", back_populates="character", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="character", cascade="all, delete-orphan")
    chat_histories = relationship("StoryChatHistory", back_populates="character", cascade="all, delete-orphan")

class CharacterImage(BaseModel):
    __tablename__ = "character_images"
    
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    image_url = Column(String(255), nullable=False)
    offset = Column(Integer, nullable=False)
    bounty = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    character = relationship("Character", back_populates="images")
    chat_histories = relationship("StoryChatHistory", back_populates="character_image")

class StoryUserMatch(BaseModel):
    __tablename__ = "story_user_matches"
    
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_name_in_story = Column(String(255), nullable=False)
    progress = Column(Integer, nullable=False)
    intimacy = Column(Integer, nullable=False)

    # Relationships
    story = relationship("Story", back_populates="user_matches")
    user = relationship("User", back_populates="story_matches")

class StoryChatHistory(BaseModel):
    __tablename__ = "story_chat_histories"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    character_image_id = Column(Integer, ForeignKey("character_images.id"), nullable=True)
    contents = Column(Text, nullable=False)
    is_user_message = Column(Boolean, default=False)
    message_type = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="chat_histories")
    character = relationship("Character", back_populates="chat_histories")
    story = relationship("Story", back_populates="chat_histories")
    character_image = relationship("CharacterImage", back_populates="chat_histories")
    status = relationship("StoryChatHistoryStatus", back_populates="chat_history", cascade="all, delete-orphan")

class StoryChatHistoryStatus(BaseModel):
    __tablename__ = "story_chat_history_statuses"
    
    story_chat_history_id = Column(Integer, ForeignKey("story_chat_histories.id"), nullable=False)
    status = Column(String(255), nullable=False)
    error_message = Column(Text, nullable=True)
    elapsed_time = Column(Float, nullable=False)

    # Relationships
    chat_history = relationship("StoryChatHistory", back_populates="status")

class Chat(BaseModel):
    __tablename__ = "chats"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    title = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User")
    character = relationship("Character", back_populates="chats")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_user_message = Column(Boolean, default=False)
    
    # Relationship
    user = relationship("User", back_populates="messages")


