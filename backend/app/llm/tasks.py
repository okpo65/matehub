from celery_app import celery_app
import time
from typing import List, Dict
from app.chat.chat_service import ChatService
from app.llm.ai_response import generate_ai_response
import asyncio
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def generate_text_llm(messages: List[Dict[str, str]],
                      model: str,
                      story_chat_history_id: int) -> dict:
    """Generate text using any LLM provider - accepts keyword arguments"""
    start_time = time.time()
    chat_service = ChatService()
    
    logger.info(f"Starting task with model: {model}, story_chat_history_id: {story_chat_history_id}")

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(generate_ai_response(
            messages=messages,
            model=model,
        ))
        
        response_time = time.time() - start_time

        chat_service.add_story_chat_history_status(
            story_chat_history_id=story_chat_history_id,
            status="completed",
            error_message=None,
            elapsed_time=response_time
        )

        chat_service.update_story_chat_history(
            story_chat_history_id=story_chat_history_id,
            contents=response
        )

        logger.info(f"Task completed successfully for story_chat_history_id: {story_chat_history_id}")
        return {
            "response": response,
            "response_time": response_time
        }
    
    except Exception as e:
        response_time = time.time() - start_time
        error_message = str(e)
        
        logger.error(f"Task failed for story_chat_history_id: {story_chat_history_id}, error: {error_message}")
        
        chat_service.add_story_chat_history_status(
            story_chat_history_id=story_chat_history_id,
            status="failed",
            error_message=error_message,
            elapsed_time=response_time
        )
        raise

@celery_app.task
def generate_summarization(model: str, user_id: int, story_id: int) -> dict:
    logger.info(f"Starting summarization task - model: {model}, user_id: {user_id}, story_id: {story_id}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        chat_service = ChatService()

        chat_history = chat_service.get_user_chat_history(user_id=user_id, story_id=story_id, offset=5, max_count=5)

        messages = []
        for chat in chat_history: 
            role = "user" if chat.is_user_message else "model"
            messages.append({"role": role, "content": chat.contents})
        
        messages.append({
            "role": "system",
            "content": f"지금까지의 대화 내역을 전부 요약해줘."
        })
        
        logger.info(f"Generating response with model: {model}")
        
        response = loop.run_until_complete(generate_ai_response(
            messages=messages,
            model=model,
        ))
        
        logger.info(f"Summarization completed successfully - response length: {len(str(response))}")
        logger.info(f"SUMMARIZATION MESSAGES: {messages}")
        logger.info(f"SUMMARIZATION RESPONSE: {response}")
        
        result = {
            "status": "success",
            "response": response,
            "user_id": int(user_id),
            "story_id": int(story_id),
            "model": str(model)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Summarization task failed: {str(e)}")
        raise e