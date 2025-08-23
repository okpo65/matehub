from celery_app import celery_app
import time
import hashlib
import uuid
from typing import Optional

@celery_app.task
def create_user_account(email: str, password: str, full_name: str, username: Optional[str] = None) -> dict:
    """Create user account (simulated database operation)"""
    # Simulate account creation processing time
    time.sleep(2)
    
    # Simulate password hashing
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Generate user ID
    user_id = str(uuid.uuid4())
    
    # Simulate user creation
    user_data = {
        "id": user_id,
        "email": email,
        "password_hash": password_hash,
        "full_name": full_name,
        "username": username or email.split("@")[0],
        "is_verified": False,
        "created_at": time.time(),
        "status": "created"
    }
    
    # Simulate sending welcome email
    send_welcome_email.delay(email, full_name)
    
    return user_data

@celery_app.task
def send_welcome_email(email: str, full_name: str) -> dict:
    """Send welcome email to new user"""
    time.sleep(1)
    
    return {
        "email": email,
        "full_name": full_name,
        "subject": "Welcome to MateHub!",
        "message": f"Welcome {full_name}! Your account has been created successfully.",
        "sent_at": time.time(),
        "status": "sent"
    }

@celery_app.task
def send_verification_email(email: str, verification_code: str) -> dict:
    """Send email verification code"""
    time.sleep(1)
    
    return {
        "email": email,
        "verification_code": verification_code,
        "subject": "Verify your email address",
        "message": f"Your verification code is: {verification_code}",
        "sent_at": time.time(),
        "status": "sent"
    }

@celery_app.task
def send_password_reset_email(email: str) -> dict:
    """Send password reset email"""
    time.sleep(1)
    
    # Generate reset token
    reset_token = str(uuid.uuid4())
    
    return {
        "email": email,
        "reset_token": reset_token,
        "subject": "Password Reset Request",
        "message": f"Click the link to reset your password: /reset-password?token={reset_token}",
        "sent_at": time.time(),
        "expires_at": time.time() + 3600,  # 1 hour
        "status": "sent"
    }

@celery_app.task
def validate_user_credentials(email: str, password: str) -> dict:
    """Validate user login credentials"""
    time.sleep(1)
    
    # Simulate credential validation
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Simulate database lookup (replace with actual database query)
    if email == "test@example.com":
        return {
            "email": email,
            "is_valid": True,
            "user_id": "user_123",
            "last_login": time.time(),
            "status": "authenticated"
        }
    else:
        return {
            "email": email,
            "is_valid": False,
            "status": "invalid_credentials"
        }
