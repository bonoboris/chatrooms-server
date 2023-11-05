"""Rooms related routes."""

import asyncio
import types
from typing import ClassVar, Self

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from chatrooms import auth, database, schemas
from chatrooms.database.connections import DB
from chatrooms.routers.commons import Pagination, default_errors, utcnow

router = APIRouter(
    prefix="/rooms",
    tags=["rooms"],
    responses=default_errors(401),
)


@router.get("/")
async def get_all_rooms(db: DB, page: Pagination, _user: auth.ActiveUser) -> list[schemas.Room]:
    """Get all rooms."""
    return await database.rooms.get_rooms(db=db, **page.model_dump())


@router.post("/", status_code=status.HTTP_201_CREATED, responses=default_errors(403))
async def create_room(db: DB, user: auth.ActiveUser, data: schemas.RoomIn) -> schemas.Room:
    """Create a new room item."""
    return await database.rooms.create_room(
        db=db, room=data, created_by=user.id, created_at=utcnow()
    )


@router.get("/{room_id}", responses=default_errors(404))
async def get_one_rooms(db: DB, room_id: int, _user: auth.ActiveUser) -> schemas.Room | None:
    """Get a room."""
    return await database.rooms.get_room_by_id(db=db, room_id=room_id)


class WebsocketManager:
    """Room websocket manager."""

    __CONNECTIONS: ClassVar[dict[str, list["WebsocketManager"]]] = {}

    EventIn = schemas.RoomWebsocketIn
    EventOut = schemas.RoomWebsocketOut
    EnterLeaveData = schemas.RoomWebsocketOutEnterLeaveData
    EventOutEnter = schemas.RoomWebsocketOutEnter
    EventOutLeave = schemas.RoomWebsocketOutLeave
    EventOutMessage = schemas.RoomWebsocketOutMessage

    def __init__(self, ws: WebSocket, room_id: str, user: schemas.User) -> None:
        self.ws = ws
        self.room_id = room_id
        self.user = user

    @property
    def room_connections(self) -> list[Self]:
        """Current connections in the room."""
        return self.__CONNECTIONS.setdefault(self.room_id, [])

    @property
    def room_users(self) -> list[int]:
        """Current users in the room."""
        return [conn.user.id for conn in self.room_connections]

    @property
    def enter_event(self) -> EventOutEnter:
        """Enter event."""
        return self.EventOutEnter(
            data=self.EnterLeaveData(user_id=self.user.id, users=self.room_users, time=utcnow())
        )

    @property
    def leave_event(self) -> EventOutLeave:
        """Leave event."""
        return self.EventOutLeave(
            data=self.EnterLeaveData(user_id=self.user.id, users=self.room_users, time=utcnow())
        )

    async def __aenter__(self) -> Self:
        """Call .connect() and return self."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool:
        """Call .disconnect()."""
        await self.disconnect()
        if exc_type == WebSocketDisconnect:
            return True
        return False

    async def connect(self) -> None:
        """Accept connection and notify all connections in the room."""
        await self.ws.accept()
        self.room_connections.append(self)
        await self.notify_all(self.enter_event, include_self=True)

    async def disconnect(self) -> None:
        """Disconnect and notify all connections in the room."""
        self.room_connections.remove(self)
        await self.notify_all(self.leave_event)

    async def receive(self) -> EventIn:
        """Await incoming event."""
        raw = await self.ws.receive_text()
        return self.EventIn.model_validate_json(raw)

    async def notify_all(
        self, event: schemas.RoomWebsocketOut, *, include_self: bool = False
    ) -> None:
        """Notify all in room."""
        payload = event.model_dump_json()
        tasks = (
            conn.ws.send_text(payload)
            for conn in self.room_connections
            if include_self or conn.user.id != self.user.id
        )
        await asyncio.gather(*tasks)

    def __repr__(self) -> str:
        """Representation of WebsocketManager ."""
        return f"WebsocketManager(user={self.user.id}, room_id={self.room_id})"


@router.websocket("/{room_id}")
async def message_websocket(
    db: DB, user: auth.WebSocketActiveUser, ws: WebSocket, room_id: str
) -> None:
    """Websocket for a room."""
    async with WebsocketManager(ws=ws, room_id=room_id, user=user) as manager:
        while True:
            event = await manager.receive()
            message = await database.messages.create_message(
                db=db, message=event.data, created_by=user.id, created_at=utcnow()
            )
            event = WebsocketManager.EventOutMessage(data=message)
            await manager.notify_all(event=event, include_self=True)
