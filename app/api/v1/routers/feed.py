from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    get_pagination_params,
)
from app.db.session import get_session
from app.schemas.posts import FeedUserItem
from app.services.posts import PostService

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=PaginatedResponse[FeedUserItem])
async def feed(
    session: Annotated[AsyncSession, Depends(get_session)],
    pagination: Annotated[PaginationParams, Depends(get_pagination_params)],
    search: Annotated[str | None, Query(max_length=255)] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
) -> PaginatedResponse[FeedUserItem]:
    return await PostService(session).list_feed(
        pagination=pagination,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )
