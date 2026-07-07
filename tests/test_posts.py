from httpx import AsyncClient

from tests.helpers import (
    PRIMARY_POST,
    PRIMARY_USER,
    SECOND_USER,
    auth_headers,
    create_comment,
    create_post,
    create_verified_user,
    register_user,
)


async def test_anonymous_user_can_list_posts(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    await create_post(client, laziz["headers"], PRIMARY_POST)

    response = await client.get("/api/v1/posts")

    assert response.status_code == 200
    assert response.json()["total"] == 1


async def test_unverified_user_cannot_create_post(client: AsyncClient) -> None:
    await register_user(client, PRIMARY_USER)
    headers = await auth_headers(
        client,
        email=PRIMARY_USER["email"],
        password=PRIMARY_USER["password"],
    )

    response = await client.post("/api/v1/posts", json=PRIMARY_POST, headers=headers)

    assert response.status_code == 403


async def test_verified_user_can_create_post(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)

    response = await client.post(
        "/api/v1/posts",
        json=PRIMARY_POST,
        headers=laziz["headers"],
    )

    assert response.status_code == 201
    assert response.json()["title"] == PRIMARY_POST["title"]


async def test_author_can_update_own_post(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)

    response = await client.patch(
        f"/api/v1/posts/{post['id']}",
        json={"title": "Medicalka backend update"},
        headers=laziz["headers"],
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Medicalka backend update"


async def test_user_cannot_update_another_users_post(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    lazizbek = await create_verified_user(client, SECOND_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)

    response = await client.patch(
        f"/api/v1/posts/{post['id']}",
        json={"title": "Lazizbek takeover attempt"},
        headers=lazizbek["headers"],
    )

    assert response.status_code == 403


async def test_author_can_delete_own_post(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)

    response = await client.delete(
        f"/api/v1/posts/{post['id']}",
        headers=laziz["headers"],
    )

    assert response.status_code == 204


async def test_user_cannot_delete_another_users_post(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    lazizbek = await create_verified_user(client, SECOND_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)

    response = await client.delete(
        f"/api/v1/posts/{post['id']}",
        headers=lazizbek["headers"],
    )

    assert response.status_code == 403


async def test_post_detail_includes_comments_and_likes(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    lazizbek = await create_verified_user(client, SECOND_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)
    comment = await create_comment(
        client,
        post_id=post["id"],
        headers=lazizbek["headers"],
    )

    like_response = await client.post(
        f"/api/v1/posts/{post['id']}/like",
        headers=lazizbek["headers"],
    )
    detail_response = await client.get(f"/api/v1/posts/{post['id']}")

    assert like_response.status_code == 201
    assert detail_response.status_code == 200
    assert detail_response.json()["comments"][0]["id"] == comment["id"]
    assert detail_response.json()["likes"] == [lazizbek["user"]["id"]]


async def test_post_update_rejects_empty_payload(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)

    response = await client.patch(
        f"/api/v1/posts/{post['id']}",
        json={},
        headers=laziz["headers"],
    )

    assert response.status_code == 422
