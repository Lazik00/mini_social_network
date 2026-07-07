from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies.maintenance import require_maintenance_token
from app.schemas.maintenance import CleanupEnqueueResponse
from app.tasks.cleanup import cleanup_expired_unverified_users_task

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.post(
    "/cleanup-unverified",
    response_model=CleanupEnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue_cleanup_unverified(
    _: Annotated[None, Depends(require_maintenance_token)],
) -> CleanupEnqueueResponse:
    task = cleanup_expired_unverified_users_task.delay()
    return CleanupEnqueueResponse(task_id=task.id)
