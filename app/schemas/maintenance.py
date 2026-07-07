from pydantic import BaseModel


class CleanupEnqueueResponse(BaseModel):
    task_id: str
    queued: bool = True


class CleanupResult(BaseModel):
    deleted_users: int
