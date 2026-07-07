from httpx import AsyncClient

from tests.helpers import (
    PRIMARY_POST,
    PRIMARY_USER,
    SECOND_USER,
    THIRD_USER,
    auth_headers,
    create_comment,
    create_post,
    create_verified_user,
    register_user,
)


async def test_anonymous_and_unverified_user_cannot_create_comment(
    client: AsyncClient,
) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)

    anonymous_response = await client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "Medicalka anonymous comment attempt."},
    )
    assert anonymous_response.status_code == 401

    await register_user(client, SECOND_USER)
    lazizbek_headers = await auth_headers(
        client,
        email=SECOND_USER["email"],
        password=SECOND_USER["password"],
    )
    unverified_response = await client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "Lazizbek comment before verification."},
        headers=lazizbek_headers,
    )
    assert unverified_response.status_code == 403


async def test_verified_user_can_create_comment(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    lazizbek = await create_verified_user(client, SECOND_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)

    response = await client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "Lazizbek confirms the Medicalka API behavior."},
        headers=lazizbek["headers"],
    )

    assert response.status_code == 201
    assert response.json()["author_id"] == lazizbek["user"]["id"]


async def test_author_can_delete_own_comment(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    lazizbek = await create_verified_user(client, SECOND_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)
    comment = await create_comment(
        client,
        post_id=post["id"],
        headers=lazizbek["headers"],
    )

    response = await client.delete(
        f"/api/v1/posts/{post['id']}/comments/{comment['id']}",
        headers=lazizbek["headers"],
    )

    assert response.status_code == 204


async def test_user_cannot_delete_another_users_comment(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    lazizbek = await create_verified_user(client, SECOND_USER)
    medicalka = await create_verified_user(client, THIRD_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)
    comment = await create_comment(
        client,
        post_id=post["id"],
        headers=lazizbek["headers"],
    )

    response = await client.delete(
        f"/api/v1/posts/{post['id']}/comments/{comment['id']}",
        headers=medicalka["headers"],
    )

    assert response.status_code == 403
