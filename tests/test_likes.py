from httpx import AsyncClient

from tests.helpers import (
    PRIMARY_POST,
    PRIMARY_USER,
    SECOND_USER,
    THIRD_USER,
    auth_headers,
    create_post,
    create_verified_user,
    register_user,
)


async def test_unverified_authenticated_user_can_like_post(
    client: AsyncClient,
) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)
    await register_user(client, SECOND_USER)
    lazizbek_headers = await auth_headers(
        client,
        email=SECOND_USER["email"],
        password=SECOND_USER["password"],
    )

    response = await client.post(
        f"/api/v1/posts/{post['id']}/like",
        headers=lazizbek_headers,
    )

    assert response.status_code == 201


async def test_verified_authenticated_user_can_like_post(
    client: AsyncClient,
) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    lazizbek = await create_verified_user(client, SECOND_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)

    response = await client.post(
        f"/api/v1/posts/{post['id']}/like",
        headers=lazizbek["headers"],
    )

    assert response.status_code == 201


async def test_user_cannot_like_own_post(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)

    response = await client.post(
        f"/api/v1/posts/{post['id']}/like",
        headers=laziz["headers"],
    )

    assert response.status_code == 403


async def test_user_cannot_like_same_post_twice(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    lazizbek = await create_verified_user(client, SECOND_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)

    first_response = await client.post(
        f"/api/v1/posts/{post['id']}/like",
        headers=lazizbek["headers"],
    )
    second_response = await client.post(
        f"/api/v1/posts/{post['id']}/like",
        headers=lazizbek["headers"],
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


async def test_user_can_unlike_post(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    lazizbek = await create_verified_user(client, SECOND_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)
    await client.post(f"/api/v1/posts/{post['id']}/like", headers=lazizbek["headers"])

    response = await client.delete(
        f"/api/v1/posts/{post['id']}/like",
        headers=lazizbek["headers"],
    )

    assert response.status_code == 204


async def test_user_cannot_unlike_missing_like(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    medicalka = await create_verified_user(client, THIRD_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)

    response = await client.delete(
        f"/api/v1/posts/{post['id']}/like",
        headers=medicalka["headers"],
    )

    assert response.status_code == 404
