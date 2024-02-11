"""Rooms related routes."""

import asyncio
import types
from typing import ClassVar, Self

import fastapi
from fastapi import status

from chatrooms import auth, schemas
from chatrooms.database import DB, queries
from chatrooms.routers.commons import Pagination, default_errors, utcnow

router = fastapi.APIRouter(
    prefix="/rooms",
    tags=["rooms"],
    responses=default_errors(status.HTTP_401_UNAUTHORIZED),
)


@router.get("/")
async def get_all_rooms(db: DB, page: Pagination, _user: auth.ActiveUser) -> list[schemas.Room]:
    """Get all rooms."""
    return await queries.select_all_rooms(db, limit=page.limit, offset=page.skip)


@router.post(
    "/", status_code=status.HTTP_201_CREATED, responses=default_errors(status.HTTP_403_FORBIDDEN)
)
async def create_room(db: DB, user: auth.ActiveUser, data: schemas.RoomIn) -> schemas.Room:
    """Create a new room item."""
    return await queries.insert_room(db, name=data.name, created_by=user.id, created_at=utcnow())


@router.get("/{room_id}", responses=default_errors(status.HTTP_404_NOT_FOUND))
async def get_room_by_id(db: DB, room_id: int, _user: auth.ActiveUser) -> schemas.Room | None:
    """Get one room by id."""
    room = await queries.select_room_by_id(db, id=room_id)
    if room is None:
        raise fastapi.HTTPException(status.HTTP_404_NOT_FOUND)
    return room


class WebsocketManager:
    """Room websocket manager."""

    __CONNECTIONS: ClassVar[dict[int, list[Self]]] = {}

    EventIn = schemas.RoomWebsocketIn
    EventOut = schemas.RoomWebsocketOut
    EnterLeaveData = schemas.RoomWebsocketOutEnterLeaveData
    EventOutEnter = schemas.RoomWebsocketOutEnter
    EventOutLeave = schemas.RoomWebsocketOutLeave
    EventOutMessage = schemas.RoomWebsocketOutMessage

    def __init__(self: Self, ws: fastapi.WebSocket, room_id: int, user: schemas.User) -> None:
        self.ws = ws
        self.room_id = room_id
        self.user = user

    @property
    def room_connections(self: Self) -> list[Self]:
        """Current connections in the room."""
        return self.__CONNECTIONS.setdefault(self.room_id, [])

    @property
    def room_users(self: Self) -> list[int]:
        """Current users in the room."""
        return [conn.user.id for conn in self.room_connections]

    @property
    def enter_event(self: Self) -> EventOutEnter:
        """Enter event."""
        return self.EventOutEnter(
            data=self.EnterLeaveData(user_id=self.user.id, users=self.room_users, time=utcnow())
        )

    @property
    def leave_event(self: Self) -> EventOutLeave:
        """Leave event."""
        return self.EventOutLeave(
            data=self.EnterLeaveData(user_id=self.user.id, users=self.room_users, time=utcnow())
        )

    async def __aenter__(self: Self) -> Self:
        """Call .connect() and return self."""
        await self.connect()
        return self

    async def __aexit__(
        self: Self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool:
        """Call .disconnect()."""
        await self.disconnect()
        if exc_type == fastapi.WebSocketDisconnect:
            return True
        return False

    async def connect(self: Self) -> None:
        """Accept connection and notify all connections in the room."""
        await self.ws.accept()
        self.room_connections.append(self)
        await self.notify_all(self.enter_event, include_self=True)

    async def disconnect(self: Self) -> None:
        """Disconnect and notify all connections in the room."""
        self.room_connections.remove(self)
        await self.notify_all(self.leave_event)

    async def receive(self: Self) -> EventIn:
        """Await incoming event."""
        raw = await self.ws.receive_text()
        return self.EventIn.model_validate_json(raw)

    async def notify_all(
        self: Self, event: schemas.RoomWebsocketOut, *, include_self: bool = False
    ) -> None:
        """Notify all in room."""
        payload = event.model_dump_json()
        tasks = (
            conn.ws.send_text(payload)
            for conn in self.room_connections
            if include_self or conn.user.id != self.user.id
        )
        await asyncio.gather(*tasks)

    def __repr__(self: Self) -> str:
        """Representation of WebsocketManager ."""
        return f"WebsocketManager(user={self.user.id}, room_id={self.room_id})"


@router.websocket("/{room_id}")
async def message_websocket(
    db: DB, user: auth.WebSocketActiveUser, ws: fastapi.WebSocket, room_id: int
) -> None:
    """Websocket for a room."""
    async with WebsocketManager(ws=ws, room_id=room_id, user=user) as manager:
        while True:
            event = await manager.receive()
            message = await queries.insert_message(
                db,
                content=event.data.content,
                room_id=room_id,
                created_by=user.id,
                created_at=utcnow(),
            )
            event = WebsocketManager.EventOutMessage(data=message)
            await manager.notify_all(event=event, include_self=True)
