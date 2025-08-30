from typing import List, Optional
from pydantic import BaseModel
from app.database.schemas import BaseSchema, TimestampMixin
from datetime import datetime

class ProfileResponse(BaseModel):
    nickname: str
    tag_name: str
    thumbnail_url: str
    description: str

# User Schemas
class UserBaseSchema(BaseSchema):
    name: str
    is_active: bool = True

class UserSchema(BaseModel):
    name: str
    kakao_id: str = None
    kakao_access_token: str = None
    kakao_refresh_token: str = None
    kakao_token_expires_at: datetime = None
    refresh_token: str = None
    refresh_token_expires_at: datetime = None
    is_anonymous: bool = True
    is_active: bool = True

class UserSchema(UserBaseSchema, TimestampMixin):
    pass

class UserWithProfilesSchema(UserBaseSchema, TimestampMixin):
    profiles: List["ProfileBaseSchema"] = []

# Profile Schemas
class ProfileBaseSchema(BaseSchema):
    user_id: int
    nickname: str
    thumbnail_url: str

class ProfileSchema(ProfileBaseSchema, TimestampMixin):
    user: Optional[UserBaseSchema] = None

UserWithProfilesSchema.model_rebuild()