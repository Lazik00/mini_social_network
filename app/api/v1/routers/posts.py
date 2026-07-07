from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, get_current_verified_user
from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    get_pagination_params,
)
from app.db.session import get_session
from app.models.user import User
from app.schemas.comments import CommentCreate, CommentRead
from app.schemas.likes import LikeRead
from app.schemas.posts import PostCreate, PostDetail, PostRead, PostUpdate
from app.services.comments import CommentService
from app.services.likes import LikeService
from app.services.posts import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PaginatedResponse[PostRead])
async def list_posts(
    session: Annotated[AsyncSession, Depends(get_session)],
    pagination: Annotated[PaginationParams, Depends(get_pagination_params)],
    search: Annotated[str | None, Query(max_length=255)] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
) -> PaginatedResponse[PostRead]:
    return await PostService(session).list_posts(
        pagination=pagination,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: PostCreate,
    user: Annotated[User, Depends(get_current_verified_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PostRead:
    return await PostService(session).create_post(user=user, data=payload)


@router.get("/{post_id}", response_model=PostDetail)
async def get_post(
    post_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PostDetail:
    return await PostService(session).get_post_detail(post_id)


@router.patch("/{post_id}", response_model=PostRead)
async def update_post(
    post_id: UUID,
    payload: PostUpdate,
    user: Annotated[User, Depends(get_current_verified_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PostRead:
    return await PostService(session).update_post(
        post_id=post_id,
        user=user,
        data=payload,
    )


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    user: Annotated[User, Depends(get_current_verified_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    await PostService(session).delete_post(post_id=post_id, user=user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{post_id}/comments", response_model=list[CommentRead])
async def list_comments(
    post_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[CommentRead]:
    return await CommentService(session).list_comments(post_id)


@router.post(
    "/{post_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    post_id: UUID,
    payload: CommentCreate,
    user: Annotated[User, Depends(get_current_verified_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CommentRead:
    return await CommentService(session).create_comment(
        post_id=post_id,
        user=user,
        data=payload,
    )


@router.delete(
    "/{post_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment(
    post_id: UUID,
    comment_id: UUID,
    user: Annotated[User, Depends(get_current_verified_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    await CommentService(session).delete_comment(
        post_id=post_id,
        comment_id=comment_id,
        user=user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{post_id}/like", response_model=LikeRead, status_code=status.HTTP_201_CREATED
)
async def like_post(
    post_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LikeRead:
    return await LikeService(session).like_post(post_id=post_id, user=user)


@router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(
    post_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    await LikeService(session).unlike_post(post_id=post_id, user=user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
