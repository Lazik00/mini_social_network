from datetime import timedelta

from httpx import AsyncClient

from app.core.time import utc_now
from tests.helpers import (
    MEDICALKA_POST,
    PRIMARY_POST,
    PRIMARY_USER,
    SECOND_POST,
    SECOND_USER,
    THIRD_USER,
    create_post,
    create_verified_user,
)


async def test_feed_returns_users_with_posts_and_likes(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    lazizbek = await create_verified_user(client, SECOND_USER)
    post = await create_post(client, laziz["headers"], PRIMARY_POST)

    like_response = await client.post(
        f"/api/v1/posts/{post['id']}/like",
        headers=lazizbek["headers"],
    )
    feed_response = await client.get("/api/v1/feed")

    assert like_response.status_code == 201
    assert feed_response.status_code == 200
    payload = feed_response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["username"] == PRIMARY_USER["username"]
    assert payload["items"][0]["posts"][0]["id"] == post["id"]
    assert payload["items"][0]["posts"][0]["likes"] == [lazizbek["user"]["id"]]


async def test_feed_pagination_works(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    lazizbek = await create_verified_user(client, SECOND_USER)
    await create_post(client, laziz["headers"], PRIMARY_POST)
    await create_post(client, lazizbek["headers"], SECOND_POST)

    response = await client.get("/api/v1/feed", params={"page": 1, "page_size": 1})

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert payload["total"] == 2
    assert len(payload["items"]) == 1


async def test_feed_search_works(client: AsyncClient) -> None:
    laziz = await create_verified_user(client, PRIMARY_USER)
    lazizbek = await create_verified_user(client, SECOND_USER)
    await create_post(client, laziz["headers"], PRIMARY_POST)
    await create_post(client, lazizbek["headers"], SECOND_POST)

    response = await client.get("/api/v1/feed", params={"search": "Lazizbek API"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["username"] == SECOND_USER["username"]
    assert payload["items"][0]["posts"][0]["title"] == SECOND_POST["title"]


async def test_feed_date_filters_work(client: AsyncClient) -> None:
    medicalka = await create_verified_user(client, THIRD_USER)
    await create_post(client, medicalka["headers"], MEDICALKA_POST)

    future_response = await client.get(
        "/api/v1/feed",
        params={"date_from": (utc_now() + timedelta(days=1)).isoformat()},
    )
    current_response = await client.get(
        "/api/v1/feed",
        params={
            "date_from": (utc_now() - timedelta(days=1)).isoformat(),
            "date_to": (utc_now() + timedelta(days=1)).isoformat(),
        },
    )

    assert future_response.status_code == 200
    assert future_response.json()["total"] == 0
    assert current_response.status_code == 200
    assert current_response.json()["total"] == 1
