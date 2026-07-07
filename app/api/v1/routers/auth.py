from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterResponse, TokenResponse
from app.schemas.users import UserCreate, UserRead
from app.services.auth import AuthService
from app.services.verification import VerificationService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RegisterResponse:
    user, verification_token = await AuthService(session).register(payload)
    return RegisterResponse(
        user=UserRead.model_validate(user),
        verification_token=verification_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    token = await AuthService(session).login(payload)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserRead)
async def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


@router.get("/verify-email", response_model=UserRead)
async def verify_email(
    session: Annotated[AsyncSession, Depends(get_session)],
    token: Annotated[str, Query(min_length=1)],
) -> User:
    return await VerificationService(session).verify_email(token)
