from celery_app import celery_app
import time
import json
from typing import Optional, List, Dict, Any
from app.llm.client_factory import LLMClientFactory
from app.database.chat_service import ChatService
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

        # Update status as completed
        chat_service.add_story_chat_history_status(
            story_chat_history_id=story_chat_history_id,
            status="completed",
            error_message=None,
            elapsed_time=response_time
        )

        # Update chat history with response
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
        
        # Update status as failed
        chat_service.add_story_chat_history_status(
            story_chat_history_id=story_chat_history_id,
            status="failed",
            error_message=error_message,
            elapsed_time=response_time
        )
        
        # Re-raise the exception so Celery marks the task as failed
        raise