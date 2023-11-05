"""Messages related routes."""

import fastapi
from fastapi import status

from chatrooms import auth, schemas
from chatrooms.database import DB, queries
from chatrooms.routers.commons import Pagination, default_errors, utcnow

router = fastapi.APIRouter(
    prefix="/messages",
    tags=["messages"],
    responses=default_errors(status.HTTP_401_UNAUTHORIZED),
    dependencies=[fastapi.Depends(auth.get_current_active_user)],
)


@router.get("/")
async def get_all_messages(
    db: DB, page: Pagination, room_id: int | None = None
) -> list[schemas.Message]:
    """Get all messages (or rooms message)."""
    if room_id is not None:
        return await queries.select_all_messages_by_room_id(
            db, room_id=room_id, limit=page.limit, offset=page.skip
        )
    return await queries.select_all_messages(db, limit=page.limit, offset=page.skip)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_message(db: DB, user: auth.ActiveUser, data: schemas.MessageIn) -> schemas.Message:
    """Create a new message item."""
    return await queries.insert_message(
        db, content=data.content, room_id=data.room_id, created_by=user.id, created_at=utcnow()
    )
