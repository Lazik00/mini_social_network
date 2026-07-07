from copy import deepcopy
from typing import Any

from httpx import AsyncClient

PRIMARY_USER: dict[str, str] = {
    "email": "lazizyunusov@gmail.com",
    "username": "lazizyunusov",
    "full_name": "Laziz Yunusov",
    "password": "Laziz123",
}

SECOND_USER: dict[str, str] = {
    "email": "lazizbek@gmail.com",
    "username": "lazizbek",
    "full_name": "Lazizbek",
    "password": "Lazizbek123",
}

THIRD_USER: dict[str, str] = {
    "email": "medicalka.test@gmail.com",
    "username": "medicalka_user",
    "full_name": "Medicalka User",
    "password": "Medicalka123",
}

PRIMARY_POST: dict[str, str] = {
    "title": "Medicalka backend notes",
    "content": "Laziz shares implementation notes for the Medicalka social feed.",
}

SECOND_POST: dict[str, str] = {
    "title": "Lazizbek API checklist",
    "content": "Lazizbek reviews pagination, permissions, and background cleanup.",
}

MEDICALKA_POST: dict[str, str] = {
    "title": "Medicalka launch plan",
    "content": "Medicalka User prepares the first public launch update.",
}


def user_payload(user: dict[str, str]) -> dict[str, str]:
    return deepcopy(user)


async def register_user(
    client: AsyncClient,
    user: dict[str, str] | None = None,
    **overrides: str,
) -> dict[str, Any]:
    payload = user_payload(user or PRIMARY_USER)
    payload.update(overrides)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def login_user(
    client: AsyncClient,
    *,
    email: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> str:
    payload: dict[str, str] = {"password": password or PRIMARY_USER["password"]}
    if email:
        payload["email"] = email
    if username:
        payload["username"] = username
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


async def login_tokens(
    client: AsyncClient,
    *,
    email: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> dict[str, str]:
    payload: dict[str, str] = {"password": password or PRIMARY_USER["password"]}
    if email:
        payload["email"] = email
    if username:
        payload["username"] = username
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


async def auth_headers(
    client: AsyncClient,
    *,
    email: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> dict[str, str]:
    token = await login_user(
        client,
        email=email,
        username=username,
        password=password,
    )
    return {"Authorization": f"Bearer {token}"}


async def verify_registration(
    client: AsyncClient,
    registration: dict[str, Any],
) -> dict[str, Any]:
    response = await client.get(
        "/api/v1/auth/verify-email",
        params={"token": registration["verification_token"]},
    )
    assert response.status_code == 200, response.text
    return response.json()


async def create_verified_user(
    client: AsyncClient,
    user: dict[str, str] | None = None,
) -> dict[str, Any]:
    selected_user = user or PRIMARY_USER
    registration = await register_user(client, selected_user)
    verified_user = await verify_registration(client, registration)
    headers = await auth_headers(
        client,
        email=selected_user["email"],
        password=selected_user["password"],
    )
    return {
        "user": verified_user,
        "headers": headers,
        "verification_token": registration["verification_token"],
    }


async def create_post(
    client: AsyncClient,
    headers: dict[str, str],
    payload: dict[str, str] | None = None,
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/posts",
        json=payload or PRIMARY_POST,
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


async def create_comment(
    client: AsyncClient,
    *,
    post_id: str,
    headers: dict[str, str],
    content: str = "Lazizbek confirms the Medicalka comment flow.",
) -> dict[str, Any]:
    response = await client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"content": content},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()
