from typing import List, Optional
from app.database.schemas import BaseSchema, TimestampMixin


# User Schemas
class UserBaseSchema(BaseSchema):
    name: str
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