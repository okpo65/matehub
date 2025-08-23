#!/usr/bin/env python3
"""
Database Setup Script
Creates PostgreSQL database and tables for MateHub
"""

import asyncio
import sys
from app.database.connection import create_tables, get_db_session
from app.database.chat_service import ChatService
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Setup database tables and initial data"""
    try:
        logger.info("Setting up database...")
        logger.info(f"Database URL: {settings.database_url}")
        
        # Create tables
        create_tables()
        logger.info("✅ Database tables created successfully")
        
        # Test database connection
        with ChatService() as chat_service:
            # Create a test user
            test_user = chat_service.get_or_create_user(
                email="test@example.com",
                full_name="Test User",
                username="testuser"
            )
            logger.info(f"✅ Test user created: {test_user.email}")
            
            # Create a test chat
            test_chat = chat_service.create_chat(
                user_id=test_user.id,
                title="Test Chat",
                model="llama3.2",
                system_prompt="You are a helpful AI assistant.",
                character="Friendly Assistant"
            )
            logger.info(f"✅ Test chat created: {test_chat.id}")
            
            # Add test messages
            chat_service.add_message(
                chat_id=test_chat.id,
                user_id=test_user.id,
                message_type="user",
                content="Hello, how are you?"
            )
            
            chat_service.add_message(
                chat_id=test_chat.id,
                user_id=test_user.id,
                message_type="assistant",
                content="Hello! I'm doing well, thank you for asking. How can I help you today?",
                model_used="llama3.2",
                tokens_used=20,
                response_time=1.5
            )
            logger.info("✅ Test messages added")
            
            # Test retrieving chat history
            history = chat_service.get_recent_chat_history(test_chat.id)
            logger.info(f"✅ Retrieved {len(history)} messages from chat history")
            
            # Get user stats
            stats = chat_service.get_user_stats(test_user.id)
            logger.info(f"✅ User stats: {stats}")
        
        logger.info("🎉 Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False

def test_database_operations():
    """Test various database operations"""
    try:
        logger.info("Testing database operations...")
        
        with ChatService() as chat_service:
            # Test user operations
            user = chat_service.get_or_create_user("demo@example.com", "Demo User")
            logger.info(f"User created/retrieved: {user.email}")
            
            # Test chat operations
            chat = chat_service.create_chat(
                user_id=user.id,
                title="Demo Chat",
                model="llama3.2"
            )
            logger.info(f"Chat created: {chat.title}")
            
            # Test message operations
            msg1 = chat_service.add_message(
                chat_id=chat.id,
                user_id=user.id,
                message_type="user",
                content="What is Python?"
            )
            
            msg2 = chat_service.add_message(
                chat_id=chat.id,
                user_id=user.id,
                message_type="assistant",
                content="Python is a high-level programming language...",
                model_used="llama3.2",
                tokens_used=50,
                response_time=2.1
            )
            
            # Test history retrieval
            history = chat_service.get_chat_history(chat.id)
            logger.info(f"Chat history: {len(history)} messages")
            
            # Test user chats
            user_chats = chat_service.get_user_chats(user.id)
            logger.info(f"User has {len(user_chats)} chats")
            
            # Test model usage logging
            usage = chat_service.log_model_usage(
                user_id=user.id,
                model_name="llama3.2",
                tokens_used=50,
                response_time=2.1,
                success=True
            )
            logger.info(f"Model usage logged: {usage.model_name}")
            
        logger.info("✅ All database operations tested successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database operations test failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 MateHub Database Setup")
    print("=" * 50)
    
    # Setup database
    if not setup_database():
        print("❌ Database setup failed")
        sys.exit(1)
    
    # Test operations
    if not test_database_operations():
        print("❌ Database operations test failed")
        sys.exit(1)
    
    print("\n✅ Database setup and testing completed successfully!")
    print("\n📝 Next steps:")
    print("1. Start PostgreSQL server")
    print("2. Update .env file with correct database credentials")
    print("3. Start the FastAPI server: ./start.sh")
    print("4. Test the new database-backed chat endpoints")

if __name__ == "__main__":
    main()
