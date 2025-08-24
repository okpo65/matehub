from pydantic import BaseModel, ConfigDict
from datetime import datetime

# Base Pydantic Models
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class TimestampMixin(BaseModel):
    id: int
    created_at: datetime
