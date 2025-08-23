from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.llm.tasks import (
    generate_text_llm
)
from app.llm.client_factory import LLMClientFactory
from app.signin.router import verify_token
from app.config import settings
from celery_app import celery_app
from celery.result import AsyncResult
from app.database.chat_service import ChatService
import json
import asyncio

router = APIRouter(prefix="/llm", tags=["LLM"])

class LLMRequest(BaseModel):
    prompt: str
    model: Optional[str] = "llama3.2"
    provider: Optional[str] = None  # Auto-detect if not specified
    max_tokens: Optional[int] = settings.max_tokens
    temperature: Optional[float] = 0.7
    system_prompt: Optional[str] = None
    user_id: Optional[int] = None

class LLMResponse(BaseModel):
    story_chat_history_id: int
    status: str
    message: str

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = None
    character_id: Optional[int] = None
    story_id: Optional[int] = None

    model: Optional[str] = "gemma3:12b"
    provider: Optional[str] = None  # Auto-detect if not specified

class ChatHistoryResponse(BaseModel):
    user_id: int
    character_id: int
    story_id: int
    contents: str
    is_user_message: bool
    message_type: str

class ChatHistoryStatusResponse(BaseModel):
    story_chat_history_id: int
    status: str
    error_message: Optional[str] = None
    elapsed_time: float

class ModelPullRequest(BaseModel):
    model_name: str

@router.get("/providers")
async def list_providers():
    """List available LLM providers and their status"""
    try:
        return LLMClientFactory.get_available_providers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check providers: {str(e)}")

@router.get("/models")
async def list_models():
    """List available LLM models"""
    return LLMClientFactory.get_available_models()

@router.get("/chat_history/{story_chat_history_id}")
async def get_chat_history(story_chat_history_id: int):
    """Get the chat history"""
    chat_service = ChatService()
    chat_history = chat_service.get_story_chat_history_by_id(story_chat_history_id)
    return ChatHistoryResponse(
        user_id=chat_history.user_id,
        character_id=chat_history.character_id,
        story_id=chat_history.story_id,
        contents=chat_history.contents,
        is_user_message=chat_history.is_user_message,
        message_type=chat_history.message_type
    )

@router.get("/chat_history_status/{story_chat_history_id}")
async def get_chat_history_status(story_chat_history_id: int):
    """Get the status of a chat history"""
    try:
        chat_service = ChatService()
        status = chat_service.get_story_chat_history_status(story_chat_history_id)
    
        return ChatHistoryStatusResponse(
            story_chat_history_id=story_chat_history_id,
            status=status.status,
            error_message=status.error_message,
            elapsed_time=status.elapsed_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat history status: {str(e)}")

@router.post("/chat", response_model=LLMResponse)
async def chat_with_llm(request: ChatRequest):
    """Chat with LLM - supports multiple providers"""
    try:
        print(f"Chat request received: {request}")
        
        # Validate required fields
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Use default values for optional fields
        user_id = request.user_id or 1
        character_id = request.character_id or 1
        story_id = request.story_id or 1
        model = request.model or "gemini-2.0-flash-lite"
        provider = request.provider or "gemini"
        
        print(f"Using IDs - User: {user_id}, Character: {character_id}, Story: {story_id}")
        print(f"Model: {model}, Provider: {provider}")
        print(f"Request model: {request.model}")
        print(f"Final model: {model}")
        
        # Initialize chat service with proper error handling
        try:
            chat_service = ChatService()
        except Exception as e:
            print(f"Failed to initialize ChatService: {e}")
            raise HTTPException(status_code=500, detail="Database connection failed")

        # Add user message to database
        try:
            chat_service.add_message(
                user_id=user_id,
                character_id=character_id,
                story_id=story_id,
                message=request.message,
                character_image_id=None,
                message_type="text",
                is_user_message=True
            )
            print("User message added to database")
        except Exception as e:
            print(f"Failed to add message to database: {e}")
            # Continue without database - don't fail the entire request
            pass

        # Build messages for LLM
        messages = []
        
        # Get character system prompt
        character = chat_service.get_character(character_id)
        messages.append({"role": "user", "content": f"{character.system_prompt}\n\n이제부터 위의 캐릭터로 완벽하게 연기하며 대화하세요."})
        messages.append({"role": "model", "content": f"네, 알겠습니다. 지금부터 {character.description} 역할로 대화하겠습니다."})
        # Get chat history
        try:
            chat_history = chat_service.get_user_chat_history(user_id, story_id, max_count=5)
            if chat_history:
                for chat in chat_history: 
                    role = "user" if chat.is_user_message else "model"
                    messages.append({"role": role, "content": chat.contents})
                print(f"Added {len(chat_history)} messages from chat history")
        except Exception as e:
            print(f"Failed to get chat history: {e}")
            # Continue without history

        # Add current message
        messages.append({"role": "user", "content": request.message})
        
        # Submit task to Celery
        try:
            story_chat_history = chat_service.add_message(
                user_id=user_id,
                character_id=character_id,
                story_id=story_id,
                message="",
                character_image_id=None,
                message_type="text",
                is_user_message=False
            )
            chat_service.add_story_chat_history_status(
                story_chat_history_id=story_chat_history.id,
                status="pending",
                error_message=None,
                elapsed_time=0
            )

            # Use appropriate task based on model
            task = generate_text_llm.delay(
                messages=messages,
                model=model,
                story_chat_history_id=story_chat_history.id
            )
            print(f"Task submitted with ID: {task.id}")
        
            return LLMResponse(
                story_chat_history_id=story_chat_history.id,
                status="pending",
                message=f"Chat message processing with {model}: {request.message[:50]}..." 
            )
        except Exception as e:
            print(f"Failed to submit Celery task: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to submit processing task: {str(e)}")
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Unexpected error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")