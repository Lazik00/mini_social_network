from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.comments import CommentRead


class PostCreate(BaseModel):
    title: str = Field(min_length=5, max_length=255)
    content: str = Field(min_length=1, max_length=10_000)


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=255)
    content: str | None = Field(default=None, min_length=1, max_length=10_000)

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "PostUpdate":
        if self.title is None and self.content is None:
            raise ValueError("At least one of title or content must be provided")
        return self


class PostRead(BaseModel):
    id: UUID
    author_id: UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    likes_count: int
    comments_count: int

    model_config = ConfigDict(from_attributes=True)


class PostDetail(PostRead):
    comments: list[CommentRead]
    likes: list[UUID]


class FeedPostItem(BaseModel):
    id: UUID
    title: str
    content: str
    likes: list[UUID]


class FeedUserItem(BaseModel):
    username: str
    posts: list[FeedPostItem]
