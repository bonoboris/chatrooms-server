"""Messages related routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from chatrooms import auth, database, schemas
from chatrooms.database.connections import DB
from chatrooms.routers.commons import Pagination, default_errors, utcnow

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
    responses=default_errors(401),
    dependencies=[Depends(auth.get_current_active_user)],
)


@router.get("/")
async def get_all_messages(
    db: DB, page: Pagination, room_id: int | None = None
) -> list[schemas.Message]:
    """Get all messages (or rooms message)."""
    if room_id is not None:
        return await database.messages.get_messages_by_room_id(
            db=db, room_id=room_id, **page.model_dump()
        )
    return await database.messages.get_messages(db=db, **page.model_dump())


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_message(db: DB, user: auth.ActiveUser, data: schemas.MessageIn) -> schemas.Message:
    """Create a new message item."""
    return await database.messages.create_message(
        db=db, message=data, created_by=user.id, created_at=utcnow()
    )


@router.get("/{message_id}", responses=default_errors(403, 404))
async def get_one_message(db: DB, user: auth.ActiveUser, message_id: int) -> schemas.Message:
    """Get all messages."""
    message = await database.messages.get_message_by_id(db=db, message_id=message_id)
    if message is None:
        raise HTTPException(404, detail=f"No message found with id: {message_id}")
    if message.created_by != user.id:
        raise HTTPException(403)
    return message
