from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.llm.tasks import (
    generate_text_llm,
    generate_summarization
)
from app.llm.client_factory import LLMClientFactory
from app.config import settings
from app.chat.chat_service import ChatService
from app.api.jwt_auth import get_current_user_or_anonymous
from app.profile.services import UserService
from app.database.connection import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/llm", tags=["LLM"])

class LLMRequest(BaseModel):
    prompt: str
    model: Optional[str] = "llama3.2"
    provider: Optional[str] = None
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
    provider: Optional[str] = None

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
async def list_providers(
    db: Session = Depends(get_db)
):
    try:
        return LLMClientFactory.get_available_providers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check providers: {str(e)}")

@router.get("/models")
async def list_models(
    db: Session = Depends(get_db)
):
    """List available LLM models"""
    return LLMClientFactory.get_available_models()

@router.get("/chat_history/{story_chat_history_id}")
async def get_chat_history(
    story_chat_history_id: int,
    user_id: int = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Get the chat history"""
    chat_service = ChatService(db)
    chat_history = chat_service.get_story_chat_history_by_id(story_chat_history_id)

    if chat_history.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return ChatHistoryResponse(
        user_id=user_id,
        character_id=chat_history.character_id,
        story_id=chat_history.story_id,
        contents=chat_history.contents,
        is_user_message=chat_history.is_user_message,
        message_type=chat_history.message_type
    )

@router.get("/chat_history_status/{story_chat_history_id}")
async def get_chat_history_status(
    story_chat_history_id: int,
    db: Session = Depends(get_db)
):
    """Get the status of a chat history"""
    try:
        chat_service = ChatService(db)
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
async def chat_with_llm(
    request: ChatRequest,
    user_id: int = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Chat with LLM - supports multiple providers"""
    try:
        print(f"Chat request received: {request}")
        
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        story_id = request.story_id or 1
        model = request.model or "gemini-2.0-flash-lite"
        provider = request.provider or "gemini"
        
        print(f"Using IDs - User: {user_id}, Story: {story_id}")
        print(f"Model: {model}, Provider: {provider}")
        print(f"Request model: {request.model}")
        print(f"Final model: {model}")
        
        try:
            chat_service = ChatService()
        except Exception as e:
            print(f"Failed to initialize ChatService: {e}")
            raise HTTPException(status_code=500, detail="Database connection failed")

        story = chat_service.get_story(story_id)
        try:
            chat_service.add_message(
                user_id=user_id,
                character_id=story.character_id,
                story_id=story_id,
                message=request.message,
                character_image_id=None,
                message_type="text",
                is_user_message=True
            )
            print("User message added to database")
        except Exception as e:
            print(f"Failed to add message to database: {e}")
            pass

        # try:
        #     summary_task = generate_summarization.delay(
        #         model='gemma3:12b',
        #         user_id=user_id,
        #         story_id=story_id
        #     )
        #     print(f"Summarization task submitted with ID: {summary_task.id}")    
        # except Exception as summary_error:
        #     print(f"Failed to submit summarization task: {summary_error}")
        #     pass

        messages = []
        
        character = chat_service.get_character(story.character_id)
        messages.append({"role": "user", "content": f"{character.system_prompt}\n\n이제부터 위의 캐릭터로 완벽하게 연기하며 대화하세요."})
        messages.append({"role": "model", "content": f"네, 알겠습니다. 지금부터 {character.description} 역할로 대화하겠습니다."})

        try:
            chat_history = chat_service.get_user_chat_history(user.id, story_id, max_count=5)
            if chat_history:
                for chat in chat_history: 
                    role = "user" if chat.is_user_message else "model"
                    messages.append({"role": role, "content": chat.contents})
                print(f"Added {len(chat_history)} messages from chat history")
        except Exception as e:
            print(f"Failed to get chat history: {e}")

        messages.append({"role": "user", "content": request.message})        

        story_chat_history = chat_service.add_message(
            user_id=user_id,
            character_id=story.character_id,
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
        try:
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

    except Exception as e:
        print(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")