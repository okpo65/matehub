"""
Clear all data from database tables
Run with: python clear_all_data.py
"""
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import (
    StoryChatHistoryStatus,
    StoryChatHistory,
    StoryUserMatch,
    CharacterImage,
    Story,
    Character,
    UserSession,
    Profile,
    ChatMessage,
    Chat,
    User
)

def clear_all_data():
    """Clear all data from all tables in correct order (respecting foreign keys)"""
    db = next(get_db())
    
    try:
        print("🗑️  Clearing all data from database tables...")
        print("=" * 50)
        
        # Delete in reverse dependency order to avoid foreign key constraints
        tables_to_clear = [
            (StoryChatHistoryStatus, "story_chat_history_statuses"),
            (StoryChatHistory, "story_chat_histories"),
            (StoryUserMatch, "story_user_matches"),
            (CharacterImage, "character_images"),
            (Story, "stories"),
            (Character, "characters"),
            (UserSession, "user_sessions"),
            (Profile, "profiles"),
            (ChatMessage, "chat_messages"),
            (Chat, "chats"),
            (User, "users")
        ]
        
        total_deleted = 0
        
        for model, table_name in tables_to_clear:
            # Count records before deletion
            count_before = db.query(model).count()
            
            if count_before > 0:
                # Delete all records
                deleted = db.query(model).delete()
                db.commit()
                
                print(f"✅ {table_name}: {deleted} records deleted")
                total_deleted += deleted
            else:
                print(f"⚪ {table_name}: already empty")
        
        print("=" * 50)
        print(f"🎉 All data cleared successfully!")
        print(f"📊 Total records deleted: {total_deleted}")
        
        # Verify all tables are empty
        print("\n🔍 Verification:")
        all_empty = True
        for model, table_name in tables_to_clear:
            count = db.query(model).count()
            if count == 0:
                print(f"✅ {table_name}: empty")
            else:
                print(f"❌ {table_name}: still has {count} records")
                all_empty = False
        
        if all_empty:
            print("\n✅ All tables are now empty!")
        else:
            print("\n❌ Some tables still have data!")
            
        return all_empty
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing data: {e}")
        return False
    finally:
        db.close()

def reset_sequences():
    """Reset auto-increment sequences to start from 1"""
    db = next(get_db())
    
    try:
        print("\n🔄 Resetting auto-increment sequences...")
        
        sequences = [
            "users_id_seq",
            "user_sessions_id_seq", 
            "profiles_id_seq",
            "characters_id_seq",
            "character_images_id_seq",
            "stories_id_seq",
            "story_user_matches_id_seq",
            "story_chat_histories_id_seq",
            "story_chat_history_statuses_id_seq",
            "chats_id_seq",
            "chat_messages_id_seq"
        ]
        
        for seq in sequences:
            try:
                db.execute(f"ALTER SEQUENCE {seq} RESTART WITH 1")
                print(f"✅ {seq}: reset to 1")
            except Exception as e:
                print(f"⚠️  {seq}: {str(e)}")
        
        db.commit()
        print("✅ Sequences reset completed!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error resetting sequences: {e}")
    finally:
        db.close()

def main():
    print("🚨 WARNING: This will delete ALL data from the database!")
    print("This action cannot be undone.")
    
    # Ask for confirmation
    confirm = input("\nAre you sure you want to continue? (type 'YES' to confirm): ")
    
    if confirm != 'YES':
        print("❌ Operation cancelled.")
        return
    
    print("\n🚀 Starting database cleanup...")
    
    # Clear all data
    success = clear_all_data()
    
    if success:
        # Reset sequences
        reset_sequences()
        
        print("\n🎉 Database cleanup completed successfully!")
        print("📝 Next steps:")
        print("   1. Run setup_test_data.py to create test data")
        print("   2. Start the server and test the application")
    else:
        print("\n❌ Database cleanup failed!")

if __name__ == "__main__":
    main()
