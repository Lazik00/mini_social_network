from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.comments import CommentRead
from app.schemas.posts import FeedPostItem, FeedUserItem, PostDetail, PostRead


def comment_to_read(comment: Comment) -> CommentRead:
    return CommentRead.model_validate(comment)


def post_to_read(post: Post) -> PostRead:
    comments = post.__dict__.get("comments") or []
    likes = post.__dict__.get("likes") or []
    return PostRead(
        id=post.id,
        author_id=post.author_id,
        title=post.title,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
        likes_count=len(likes),
        comments_count=len(comments),
    )


def post_to_detail(post: Post) -> PostDetail:
    comments = post.__dict__.get("comments") or []
    likes = post.__dict__.get("likes") or []
    return PostDetail(
        **post_to_read(post).model_dump(),
        comments=[comment_to_read(comment) for comment in comments],
        likes=[like.user_id for like in likes],
    )


def user_to_feed_item(user: User) -> FeedUserItem:
    posts = user.__dict__.get("posts") or []
    return FeedUserItem(
        username=user.username,
        posts=[
            FeedPostItem(
                id=post.id,
                title=post.title,
                content=post.content,
                likes=[like.user_id for like in post.__dict__.get("likes") or []],
            )
            for post in posts
        ],
    )
