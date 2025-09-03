from sqlalchemy.orm import Session, selectinload, joinedload, load_only
from sqlalchemy import and_, desc
from typing import List, Optional
from .models import Character, Story, StoryChatHistory, StoryUserMatch, CharacterImage as CharacterImageModel
from app.character.schemas import (
    CharacterWithStoriesSchema, StoryWithCharacterSchema, StoryWithRelationsSchema,
    CharacterDetailResponse, StoryDetailResponse, StoryChatHistoryWithRelationsSchema, CharacterImageSchema, CharacterProfileResponse
)

class CharacterService:
    def __init__(self, db: Session):
        self.db = db

    def get_characters(self, limit: Optional[int] = None, include_inactive: bool = False) -> List[CharacterWithStoriesSchema]:
        """Get list of characters with their stories"""
        query = (
            self.db.query(Character)
            .options(
                load_only(
                    Character.id,
                    Character.description,
                    Character.tag_list,
                ),
                selectinload(Character.stories).load_only(
                    Story.id,
                    Story.storyline,
                    Story.description,
                    Story.background_image_url
                )
            )
        )
            
        characters = query.all()
        return [CharacterWithStoriesSchema.model_validate(char) for char in characters]

    def get_all_characters(self, limit: Optional[int] = None) -> List[CharacterWithStoriesSchema]:
        """Get all characters with their stories (including inactive)"""
        query = (
            self.db.query(Character)
            .options(
                selectinload(Character.stories),
                selectinload(Character.images)
            )
            .order_by(Character.rank)
        )
        
        if limit:
            query = query.limit(limit)
            
        characters = query.all()
        return [CharacterWithStoriesSchema.model_validate(char) for char in characters]

    def get_character_with_stories(self, character_id: int) -> Optional[CharacterWithStoriesSchema]:
        """Get character with all related stories using efficient loading"""
        character = (
            self.db.query(Character)
            .options(
                selectinload(Character.stories),
                selectinload(Character.images)
            )
            .filter(Character.id == character_id)
            .first()
        )
        
        if character:
            return CharacterWithStoriesSchema.model_validate(character)
        return None

    def get_character_story_detail(self, character_id: int) -> Optional[CharacterDetailResponse]:
        """Get complete character details with all relationships"""
        character = (
            self.db.query(Character)
            .options(
                selectinload(Character.stories),
                # selectinload(Character.images),
                # selectinload(Character.chat_histories).selectinload(StoryChatHistory.story)
            )
            .filter(Character.id == character_id)
            .first()
        )
        
        if character:
            return CharacterDetailResponse.model_validate(character)
        return None

    def get_character_profile(self, character_id: int) -> Optional[CharacterProfileResponse]:
        """Get complete character details with all relationships"""
        character = (
            self.db.query(Character)
            .options(
                selectinload(Character.stories),
                selectinload(Character.images),
                # selectinload(Character.chat_histories).selectinload(StoryChatHistory.story)
            )
            .filter(Character.id == character_id)
            .first()
        )
        
        if character:
            return CharacterProfileResponse.model_validate(character)
        return None

    def get_character_photos(self, character_id: int, active_only: bool = True) -> List[CharacterImageSchema]:
        """Get all photos for a specific character"""
        query = self.db.query(CharacterImageModel).filter(CharacterImageModel.character_id == character_id)
        
        if active_only:
            query = query.filter(CharacterImageModel.is_active == True)
        
        images = query.order_by(CharacterImageModel.offset).all()
        return [CharacterImageSchema.model_validate(img) for img in images]

    def get_popular_characters(self, limit: int = 10) -> List[CharacterWithStoriesSchema]:
        """Get popular characters with their stories"""
        characters = (
            self.db.query(Character)
            .options(
                selectinload(Character.stories),
                selectinload(Character.images)
            )
            .filter(Character.is_popular == True)
            .order_by(Character.rank)
            .limit(limit)
            .all()
        )
        
        return [CharacterWithStoriesSchema.model_validate(char) for char in characters]

class StoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_stories(self, limit: int, cursor: int = None) -> List[StoryWithCharacterSchema]:
        """Get all stories with their characters"""
        query = (
            self.db.query(Story)
            .options(
                joinedload(Story.character).selectinload(Character.images)
            )
            .order_by(Story.id)
            .filter(Story.is_active == True)
        )
        if cursor:
            query = query.filter(Story.id < cursor)

        return query.limit(limit).all()

    def get_popular_stories(self, limit: int = 10) -> List[StoryWithCharacterSchema]:
        query = (
            self.db.query(Story)
            .options(
                joinedload(Story.character).selectinload(Character.images)
            )
            .order_by(Story.id)
            .filter(Story.is_active == True)
            .filter(Story.is_popular == True)
        )
        return query.limit(limit).all()

    def get_story_with_character(self, story_id: int) -> Optional[StoryWithCharacterSchema]:
        """Get story with character information"""
        story = (
            self.db.query(Story)
            .options(
                joinedload(Story.character).selectinload(Character.images)
            )
            .filter(Story.id == story_id)
            .first()
        )
        
        if story:
            return StoryWithCharacterSchema.model_validate(story)
        return None

    

    def get_story_detail(self, story_id: int) -> Optional[StoryDetailResponse]:
        """Get complete story details with all relationships"""
        story = (
            self.db.query(Story)
            .options(
                joinedload(Story.character).selectinload(Character.images),
                selectinload(Story.user_matches).selectinload(StoryUserMatch.user),
                selectinload(Story.chat_histories).selectinload(StoryChatHistory.user)
            )
            .filter(Story.id == story_id)
            .first()
        )
        
        if story:
            return StoryDetailResponse.model_validate(story)
        return None

    def get_stories_by_character(self, character_id: int) -> List[StoryWithCharacterSchema]:
        """Get all stories for a specific character"""
        stories = (
            self.db.query(Story)
            .options(
                joinedload(Story.character).selectinload(Character.images)
            )
            .filter(
                and_(
                    Story.character_id == character_id,
                    Story.is_active == True
                )
            )
            .all()
        )
        
        return [StoryWithCharacterSchema.model_validate(story) for story in stories]

    def get_user_story_matches(self, user_id: int) -> List[StoryWithCharacterSchema]:
        """Get all stories a user has matched with"""
        matches = (
            self.db.query(StoryUserMatch)
            .options(
                joinedload(StoryUserMatch.story).joinedload(Story.character).selectinload(Character.images)
            )
            .filter(StoryUserMatch.user_id == user_id)
            .all()
        )
        
        return [StoryWithCharacterSchema.model_validate(match.story) for match in matches]

class ChatHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_chat_history_with_relations(
        self, 
        user_id: int, 
        story_id: int, 
        limit: int = 20,
        cursor: Optional[int] = None
    ) -> List[StoryChatHistoryWithRelationsSchema]:
        """Get chat history with all related information"""
        query = (
            self.db.query(StoryChatHistory)
            .options(
                joinedload(StoryChatHistory.user),
                joinedload(StoryChatHistory.character).selectinload(Character.images),
                joinedload(StoryChatHistory.story),
                joinedload(StoryChatHistory.character_image)
            )
            .filter(
                and_(
                    StoryChatHistory.user_id == user_id,
                    StoryChatHistory.story_id == story_id,
                    StoryChatHistory.is_active == True
                )
            )
        )
        
        if cursor:
            query = query.filter(StoryChatHistory.id < cursor)
        
        messages = query.order_by(StoryChatHistory.id).limit(limit).all()
        
        return [StoryChatHistoryWithRelationsSchema.model_validate(msg) for msg in messages]

    def get_latest_chat_with_character_info(
        self, 
        user_id: int, 
        story_id: int, 
        limit: int = 10
    ) -> List[StoryChatHistoryWithRelationsSchema]:
        """Get latest chat messages with character and story information"""
        messages = (
            self.db.query(StoryChatHistory)
            .options(
                joinedload(StoryChatHistory.user),
                joinedload(StoryChatHistory.character).selectinload(Character.images),
                joinedload(StoryChatHistory.story),
                joinedload(StoryChatHistory.character_image)
            )
            .filter(
                and_(
                    StoryChatHistory.user_id == user_id,
                    StoryChatHistory.story_id == story_id,
                    StoryChatHistory.is_active == True
                )
            )
            .order_by(desc(StoryChatHistory.id))
            .limit(limit)
            .all()
        )
        
        # Reverse to show oldest first
        messages.reverse()
        
        return [StoryChatHistoryWithRelationsSchema.model_validate(msg) for msg in messages]

class RelationshipQueryService:
    """Service for complex relationship queries"""
    
    def __init__(self, db: Session):
        self.db = db

    def get_character_story_stats(self, character_id: int) -> dict:
        """Get statistics about a character's stories and interactions"""
        character = (
            self.db.query(Character)
            .options(
                selectinload(Character.stories).selectinload(Story.user_matches),
                selectinload(Character.stories).selectinload(Story.chat_histories),
                selectinload(Character.images)
            )
            .filter(Character.id == character_id)
            .first()
        )
        
        if not character:
            return {}
        
        total_stories = len(character.stories)
        active_stories = len([s for s in character.stories if s.is_active])
        total_matches = sum(len(story.user_matches) for story in character.stories)
        total_messages = sum(len(story.chat_histories) for story in character.stories)
        
        return {
            "character_id": character_id,
            "character_name": character.description[:50] + "..." if len(character.description) > 50 else character.description,
            "total_stories": total_stories,
            "active_stories": active_stories,
            "total_user_matches": total_matches,
            "total_chat_messages": total_messages,
            "total_images": len(character.images),
            "is_popular": character.is_popular,
            "rank": character.rank
        }

    def get_story_engagement_stats(self, story_id: int) -> dict:
        """Get engagement statistics for a story"""
        story = (
            self.db.query(Story)
            .options(
                joinedload(Story.character),
                selectinload(Story.user_matches),
                selectinload(Story.chat_histories)
            )
            .filter(Story.id == story_id)
            .first()
        )
        
        if not story:
            return {}
        
        unique_users = len(set(match.user_id for match in story.user_matches))
        total_messages = len(story.chat_histories)
        user_messages = len([msg for msg in story.chat_histories if msg.is_user_message])
        character_messages = total_messages - user_messages
        
        return {
            "story_id": story_id,
            "story_title": story.storyline[:50] + "..." if len(story.storyline) > 50 else story.storyline,
            "character_name": story.character.description[:30] + "..." if len(story.character.description) > 30 else story.character.description,
            "unique_users": unique_users,
            "total_matches": len(story.user_matches),
            "total_messages": total_messages,
            "user_messages": user_messages,
            "character_messages": character_messages,
            "is_active": story.is_active
        }
