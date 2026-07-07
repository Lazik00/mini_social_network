from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LikeRead(BaseModel):
    id: UUID
    user_id: UUID
    post_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
