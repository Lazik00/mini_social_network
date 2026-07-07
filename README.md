# Mini Social Network Backend

FastAPI backend for a mini social network: users, JWT authentication, email verification, posts, comments, likes, feed, pagination/search/date filters, and Celery-based cleanup of expired unverified users.

## Stack

- Python 3.13+
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x async
- Alembic
- Pydantic v2
- JWT access tokens
- Passlib + bcrypt
- Celery + Redis
- Docker Compose
- Pytest
- Ruff + Black

## Architecture

```text
app/
  api/v1/routers/        HTTP endpoints
  api/v1/dependencies/  auth and maintenance dependencies
  core/                 config, security, pagination, errors, logging
  db/                   SQLAlchemy base and async session
  models/               SQLAlchemy models
  schemas/              Pydantic request/response schemas
  repositories/         database access only
  services/             business logic and permissions
  tasks/                Celery app and cleanup task
migrations/             Alembic migrations
tests/                  async integration/service tests
```

Routers do not contain SQLAlchemy queries or business rules. Repositories own database access. Services own authentication, permissions, verification, posts/comments/likes rules, feed mapping, and cleanup behavior.

## Database

Main entities:

- `users`: UUID PK, unique `email`, unique `username`, password hash, verification flag, timestamps.
- `posts`: UUID PK, FK to user, title/content, timestamps.
- `comments`: UUID PK, FK to post/user, content, timestamp.
- `likes`: UUID PK, FK to post/user, unique `(user_id, post_id)`.
- `email_verification_tokens`: hashed one-time token, expiry, used marker.

Foreign keys use cascade delete where appropriate. Uniqueness is enforced in PostgreSQL, not only in application code.

## Run With Docker

Create a local `.env` from the example and replace secrets:

```bash
cp .env.example .env
```

Start everything:

```bash
docker compose up --build
```

Services:

- API: `http://localhost:8010`
- Swagger/OpenAPI: `http://localhost:8010/docs`
- PostgreSQL: internal compose service `db:5432`
- Redis: internal compose service `redis:6379`
- Celery worker: `worker`
- Celery beat: `beat`

The `app` service runs migrations before starting Uvicorn:

```bash
alembic upgrade head
```

Manual migration command, if needed:

```bash
docker compose run --rm app alembic upgrade head
```

## Environment Variables

All runtime configuration is environment-based.

```text
SOCIAL_APP_NAME=Mini Social Network
SOCIAL_ENVIRONMENT=local
SOCIAL_APP_PORT=8010
SOCIAL_DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/social
SOCIAL_REDIS_URL=redis://redis:6379/0
SOCIAL_JWT_SECRET_KEY=replace-with-a-long-random-secret
SOCIAL_JWT_ALGORITHM=HS256
SOCIAL_ACCESS_TOKEN_EXPIRE_MINUTES=30
SOCIAL_VERIFICATION_TOKEN_EXPIRE_HOURS=24
SOCIAL_CLEANUP_UNVERIFIED_AFTER_HOURS=48
SOCIAL_MAINTENANCE_TOKEN=local-maintenance-token
SOCIAL_LOGIN_RATE_LIMIT_ATTEMPTS=5
SOCIAL_LOGIN_RATE_LIMIT_WINDOW_SECONDS=900
SOCIAL_PUBLIC_BASE_URL=http://localhost:8010
SOCIAL_SMTP_HOST=
SOCIAL_SMTP_PORT=587
SOCIAL_SMTP_USERNAME=
SOCIAL_SMTP_PASSWORD=
SOCIAL_SMTP_FROM_EMAIL=
SOCIAL_SMTP_USE_TLS=true
SOCIAL_POST_TTL_DAYS=
```

SMTP is optional. If SMTP values are missing, the app uses `LoggingEmailSender`.
If `SOCIAL_POST_TTL_DAYS` is empty, old post cleanup is skipped safely.

## API Documentation

Swagger UI is available at:

```text
http://localhost:8010/docs
```

Main endpoints:

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
GET    /api/v1/auth/me
GET    /api/v1/auth/verify-email
PATCH  /api/v1/users/me

GET    /api/v1/posts
POST   /api/v1/posts
GET    /api/v1/posts/{post_id}
PATCH  /api/v1/posts/{post_id}
DELETE /api/v1/posts/{post_id}

GET    /api/v1/posts/{post_id}/comments
POST   /api/v1/posts/{post_id}/comments
DELETE /api/v1/posts/{post_id}/comments/{comment_id}

POST   /api/v1/posts/{post_id}/like
DELETE /api/v1/posts/{post_id}/like

GET    /api/v1/feed
POST   /api/v1/maintenance/cleanup-unverified
```

Authenticated requests use:

```text
Authorization: Bearer <ACCESS_TOKEN>
```

FastAPI/Pydantic validation errors return HTTP `422`.

## API Examples

Register:

```bash
curl -X POST http://localhost:8010/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"lazizyunusov@gmail.com","username":"lazizyunusov","full_name":"Laziz Yunusov","password":"Laziz123"}'
```

The response includes `verification_token` because SMTP is intentionally not configured for the assignment. The token is stored hashed in the database and is one-time use.
If SMTP settings are configured, the app also sends a verification link using `SMTPEmailSender`.

Verify email:

```bash
curl "http://localhost:8010/api/v1/auth/verify-email?token=<VERIFICATION_TOKEN>"
```

Login:

```bash
curl -X POST http://localhost:8010/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"lazizyunusov@gmail.com","password":"Laziz123"}'
```

Current user:

```bash
curl http://localhost:8010/api/v1/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Update profile:

```bash
curl -X PATCH http://localhost:8010/api/v1/users/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Laziz Yunusov"}'
```

Create a post:

```bash
curl -X POST http://localhost:8010/api/v1/posts \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Medicalka backend notes","content":"Laziz shares implementation notes for the Medicalka social feed."}'
```

Create a comment:

```bash
curl -X POST http://localhost:8010/api/v1/posts/<POST_ID>/comments \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"content":"Lazizbek confirms the Medicalka comment flow."}'
```

Like a post:

```bash
curl -X POST http://localhost:8010/api/v1/posts/<POST_ID>/like \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Unlike a post:

```bash
curl -X DELETE http://localhost:8010/api/v1/posts/<POST_ID>/like \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

List posts with pagination/search/date filters:

```bash
curl "http://localhost:8010/api/v1/posts?page=1&page_size=20&search=Medicalka&date_from=2026-01-01T00:00:00Z"
```

Feed:

```bash
curl "http://localhost:8010/api/v1/feed?page=1&page_size=20&search=Medicalka"
```

Enqueue cleanup manually:

```bash
curl -X POST http://localhost:8010/api/v1/maintenance/cleanup-unverified \
  -H "X-Maintenance-Token: local-maintenance-token"
```

Cleanup also runs periodically through Celery beat and worker.

Cleanup tasks:

- `cleanup_expired_unverified_users` runs hourly through Celery Beat.
- `cleanup_expired_posts` is added to Celery Beat only when `SOCIAL_POST_TTL_DAYS` is set.
- Post TTL cleanup deletes old posts; database cascade removes their comments and likes.

Login bruteforce protection:

- `/api/v1/auth/login` counts failed attempts by IP plus email/username.
- Default limit is 5 failed attempts per 15 minutes.
- Too many failures return HTTP `429`.
- Successful login clears the failure counter when Redis is available.

## Permissions

- Anonymous users can read posts and feed.
- Authenticated unverified users can read and like posts.
- Verified users can create posts and comments.
- Only resource owners can update/delete their posts and delete their comments.
- Users cannot like their own posts.
- Duplicate likes are prevented by both service logic and the database unique constraint.

## Tests And Quality

Run tests in Docker:

```bash
docker compose run --rm --no-deps app sh -c "pip install -e '.[dev]' && pytest -q"
```

Run the same quality checks used before submission:

```bash
docker compose run --rm --no-deps app sh -c "pip install -e '.[dev]' && ruff check . && black --check . && pytest -q"
```

Install pre-commit locally:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

GitHub Actions runs the same checks on `push` and `pull_request`.

Current test coverage includes:

- registration and duplicate email/username
- login by email/username, invalid login, and protected endpoint access
- login rate limiting and successful login after failed attempts
- email verification success, invalid token, expired token, and one-time behavior
- verified/unverified permissions
- post owner permissions and post detail comments/likes
- comment creation and comment owner permissions
- like/unlike rules
- feed structure, pagination, search, and date filters
- unverified user cleanup, post TTL cleanup, and Celery cleanup task wrappers
