from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from celery_app import celery_app, add_numbers, process_data
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Import routers
from app.llm.router import router as llm_router
from app.character.router import router as character_router
from app.story.router import router as story_router
from app.chat.router import router as chat_router
from app.auth.routes import router as kakao_auth_router
from app.config import settings

# Load environment variables
load_dotenv()

app = FastAPI(
    title="MateHub API",
    description="FastAPI + Celery application with LLM, Authentication, Profile, Character, and Story services",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://kauth.kakao.com",
        "https://kapi.kakao.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers
app.include_router(llm_router)
# app.include_router(auth_router)
# app.include_router(profile_router)
app.include_router(character_router)
app.include_router(story_router)
app.include_router(chat_router)
app.include_router(kakao_auth_router)

# Pydantic models for request/response
class AddRequest(BaseModel):
    x: int
    y: int

class ProcessRequest(BaseModel):
    data: str

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "MateHub API is running!",
        "services": ["LLM", "Authentication", "Profile", "Character", "Story"],
        "environment": settings.environment,
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "celery": "connected",
            "redis": "connected"
        },
        "environment": settings.environment
    }

# Legacy endpoints (keeping for backward compatibility)
@app.post("/add", response_model=TaskResponse)
async def add_task(request: AddRequest):
    """Submit an addition task to Celery"""
    task = add_numbers.delay(request.x, request.y)
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message=f"Task submitted to add {request.x} + {request.y}"
    )

@app.post("/process", response_model=TaskResponse)
async def process_task(request: ProcessRequest):
    """Submit a data processing task to Celery"""
    task = process_data.delay(request.data)
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message=f"Task submitted to process: {request.data}"
    )

@app.get("/task/{task_id}")
async def get_task_result(task_id: str):
    """Get the result of a Celery task"""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == "PENDING":
            return {
                "task_id": task_id,
                "status": "pending",
                "message": "Task is still processing",
                "current": None,
                "total": None
            }
        elif task_result.state == "SUCCESS":
            return {
                "task_id": task_id,
                "status": "success",
                "result": task_result.result,
                "message": "Task completed successfully"
            }
        elif task_result.state == "FAILURE":
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(task_result.info),
                "message": "Task failed"
            }
        elif task_result.state == "RETRY":
            return {
                "task_id": task_id,
                "status": "retry",
                "message": "Task is being retried",
                "error": str(task_result.info)
            }
        else:
            # For PROGRESS or other states
            return {
                "task_id": task_id,
                "status": task_result.state.lower(),
                "message": f"Task is in {task_result.state} state",
                "info": task_result.info
            }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Task not found: {str(e)}")

@app.get("/job_status/{task_id}")
async def job_status(task_id: str):
    """Alternative endpoint name for task status (alias for get_task_result)"""
    return await get_task_result(task_id)

@app.get("/task/{task_id}/detailed")
async def get_task_detailed_info(task_id: str):
    """Get detailed information about a task including metadata"""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        # Get task info from Redis directly
        from celery.result import AsyncResult
        
        return {
            "task_id": task_id,
            "status": task_result.state,
            "result": task_result.result if task_result.successful() else None,
            "error": str(task_result.info) if task_result.failed() else None,
            "traceback": task_result.traceback if task_result.failed() else None,
            "date_done": task_result.date_done.isoformat() if task_result.date_done else None,
            "task_name": task_result.name,
            "args": getattr(task_result, 'args', None),
            "kwargs": getattr(task_result, 'kwargs', None),
            "retries": getattr(task_result, 'retries', 0),
            "eta": getattr(task_result, 'eta', None)
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Task not found: {str(e)}")

@app.get("/tasks")
async def list_active_tasks():
    """List all active tasks"""
    active_tasks = celery_app.control.inspect().active()
    return {"active_tasks": active_tasks}
