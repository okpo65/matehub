from sqlalchemy.orm import Session, selectinload, joinedload, load_only
from sqlalchemy import and_, desc
from typing import List, Optional
from app.database.models import User, Profile
from app.profile.schemas import ProfileResponse, UserSchema
from fastapi import HTTPException


class ProfileService:
    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, user_id: int) -> Optional[Profile]:
        profile = self.db.query(Profile).filter(Profile.user_id == user_id).first()
        print(f"Profile: {profile}")
        return profile

    def update_profile(self, user_id: int, profile_data: Profile) -> Optional[Profile]:
        profile = self.db.query(Profile).filter(Profile.user_id == user_id).first()
        profile.nickname = profile_data.nickname
        profile.tag_name = profile_data.tag_name
        profile.thumbnail_url = profile_data.thumbnail_url
        profile.description = profile_data.description
        self.db.commit()
        return profile


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int) -> Optional[User]:
        user = self.db.query(User).filter(User.id == user_id).first()
        return user

    def create_user(self, user_data: UserSchema) -> Optional[User]:
        user = User(
            name=user_data.name,
            kakao_id=user_data.kakao_id,
            kakao_access_token=user_data.kakao_access_token,
            kakao_refresh_token=user_data.kakao_refresh_token,
            kakao_token_expires_at=user_data.kakao_token_expires_at,
            refresh_token=user_data.refresh_token,
            refresh_token_expires_at=user_data.refresh_token_expires_at,
            is_anonymous=user_data.is_anonymous,
            is_active=user_data.is_active
        )
        self.db.add(user)
        self.db.commit()

        profile = Profile(
            user_id=user.id,
            nickname=None,
            tag_name=None,
            thumbnail_url=None,
            description=None
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(profile)
        return user