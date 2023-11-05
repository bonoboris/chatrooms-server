"""Schemas for chatrooms app."""

from datetime import datetime
from typing import Annotated, Literal

import pydantic


class MessageIn(pydantic.BaseModel):
    """In Message schema."""

    room_id: int
    content: str


class Message(MessageIn):
    """Message schema."""

    id: int
    created_by: int
    created_at: datetime


class RoomWebsocketIn(pydantic.BaseModel):
    """Room Websocket incoming event."""

    event: Literal["message"]
    data: MessageIn


class RoomWebsocketOutMessage(pydantic.BaseModel):
    """Room Websocket outgoing message event."""

    event: Literal["message"] = "message"
    data: Message


class RoomWebsocketOutEnterLeaveData(pydantic.BaseModel):
    """Room Websocket outgoing enter/leave event data."""

    user_id: int
    users: list[int]
    time: datetime


class RoomWebsocketOutEnter(pydantic.BaseModel):
    """Room Websocket outgoing enter event."""

    event: Literal["enter"] = "enter"
    data: RoomWebsocketOutEnterLeaveData


class RoomWebsocketOutLeave(pydantic.BaseModel):
    """Room Websocket outgoing leave event."""

    event: Literal["leave"] = "leave"
    data: RoomWebsocketOutEnterLeaveData


RoomWebsocketOut = Annotated[
    RoomWebsocketOutEnter | RoomWebsocketOutLeave | RoomWebsocketOutMessage,
    pydantic.Field(discriminator="event"),
]


class RoomIn(pydantic.BaseModel):
    """Room In schema."""

    name: str


class Room(RoomIn):
    """Room schema."""

    id: int
    created_by: int
    created_at: datetime


TodoStatus = Literal["todo", "in progress", "done"]


class TodoIn(pydantic.BaseModel):
    """Todo item."""

    status: TodoStatus
    description: str


class Todo(TodoIn):
    """Todo item out."""

    id: int
    created_by: int
    created_at: datetime
    modified_at: datetime


class UserIn(pydantic.BaseModel):
    """User create schema."""

    username: str
    email: str
    password: str


class User(pydantic.BaseModel):
    """User schema."""

    id: int
    username: str
    is_active: bool
    created_at: datetime
    avatar_id: int | None = None


class UserFull(User):
    """Complete user schema."""

    email: str


class UserDB(UserFull):
    """User in DB schema."""

    digest: str


class File(pydantic.BaseModel):
    """File."""

    fs_filename: str
    filename: str
    content_type: str
    size: int
    checksum: str
    uploaded_at: datetime


class FileDB(File):
    """File in DB."""

    id: int
    user_id: int


class RoomUser(pydantic.BaseModel):
    """Room User."""

    room_id: int
    user_id: int


class RoomUserDB(RoomUser):
    """Room User in DB."""

    id: int
