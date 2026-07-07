from httpx import AsyncClient

from tests.helpers import (
    PRIMARY_USER,
    SECOND_USER,
    auth_headers,
    login_user,
    register_user,
)


async def test_successful_registration(client: AsyncClient) -> None:
    payload = await register_user(client, PRIMARY_USER)

    assert payload["user"]["email"] == PRIMARY_USER["email"]
    assert payload["user"]["username"] == PRIMARY_USER["username"]
    assert payload["user"]["full_name"] == PRIMARY_USER["full_name"]
    assert payload["user"]["is_verified"] is False
    assert "password" not in payload["user"]
    assert "password_hash" not in payload["user"]


async def test_duplicate_email(client: AsyncClient) -> None:
    await register_user(client, PRIMARY_USER)

    response = await client.post(
        "/api/v1/auth/register",
        json={
            **SECOND_USER,
            "email": PRIMARY_USER["email"],
        },
    )

    assert response.status_code == 409
    assert response.json()["success"] is False


async def test_duplicate_username(client: AsyncClient) -> None:
    await register_user(client, PRIMARY_USER)

    response = await client.post(
        "/api/v1/auth/register",
        json={
            **SECOND_USER,
            "username": PRIMARY_USER["username"],
        },
    )

    assert response.status_code == 409
    assert response.json()["success"] is False


async def test_successful_login_by_email(client: AsyncClient) -> None:
    await register_user(client, PRIMARY_USER)

    token = await login_user(
        client,
        email=PRIMARY_USER["email"],
        password=PRIMARY_USER["password"],
    )

    assert token


async def test_successful_login_by_username(client: AsyncClient) -> None:
    await register_user(client, PRIMARY_USER)

    token = await login_user(
        client,
        username=PRIMARY_USER["username"],
        password=PRIMARY_USER["password"],
    )

    assert token


async def test_invalid_login(client: AsyncClient) -> None:
    await register_user(client, PRIMARY_USER)

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": PRIMARY_USER["email"],
            "password": "WrongLaziz123",
        },
    )

    assert response.status_code == 401
    assert response.json()["success"] is False


async def test_failed_login_attempts_are_counted(
    client: AsyncClient,
    login_rate_limiter,
) -> None:
    await register_user(client, PRIMARY_USER)

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": PRIMARY_USER["email"],
            "password": "WrongLaziz123",
        },
    )

    assert response.status_code == 401
    assert sum(login_rate_limiter.attempts.values()) == 1


async def test_too_many_failed_login_attempts_returns_429(
    client: AsyncClient,
) -> None:
    await register_user(client, PRIMARY_USER)
    payload = {
        "email": PRIMARY_USER["email"],
        "password": "WrongLaziz123",
    }

    for _ in range(5):
        response = await client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 401

    blocked_response = await client.post("/api/v1/auth/login", json=payload)

    assert blocked_response.status_code == 429
    assert blocked_response.json()["success"] is False


async def test_successful_login_still_works_after_failed_attempts(
    client: AsyncClient,
    login_rate_limiter,
) -> None:
    await register_user(client, PRIMARY_USER)

    for _ in range(2):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": PRIMARY_USER["email"],
                "password": "WrongLaziz123",
            },
        )
        assert response.status_code == 401

    token = await login_user(
        client,
        email=PRIMARY_USER["email"],
        password=PRIMARY_USER["password"],
    )

    assert token
    assert sum(login_rate_limiter.attempts.values()) == 0


async def test_auth_me_with_valid_token(client: AsyncClient) -> None:
    await register_user(client, PRIMARY_USER)
    headers = await auth_headers(
        client,
        email=PRIMARY_USER["email"],
        password=PRIMARY_USER["password"],
    )

    response = await client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["username"] == PRIMARY_USER["username"]


async def test_auth_me_with_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-laziz-token"},
    )

    assert response.status_code == 401
    assert response.json()["success"] is False


async def test_auth_me_without_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["success"] is False


async def test_user_update_rejects_empty_payload(client: AsyncClient) -> None:
    await register_user(client, PRIMARY_USER)
    headers = await auth_headers(
        client,
        email=PRIMARY_USER["email"],
        password=PRIMARY_USER["password"],
    )

    response = await client.patch("/api/v1/users/me", json={}, headers=headers)

    assert response.status_code == 422
