"""Schemas for chatrooms app."""

from datetime import datetime
from typing import Annotated, Literal, Self

import psycopg.rows
import pydantic


class BaseModel(pydantic.BaseModel):
    """`pydantic.BaseModel` wrapper."""

    @classmethod
    def get_row_factory(cls) -> psycopg.rows.BaseRowFactory[Self]:
        """Get row factory for this model."""
        return psycopg.rows.class_row(cls)


class Version(BaseModel):
    """DB Version schema."""

    id: int
    version: int


class MessageIn(BaseModel):
    """In Message schema."""

    room_id: int
    content: str


class Message(MessageIn):
    """Message schema."""

    id: int
    created_by: int
    created_at: datetime


class RoomWebsocketIn(BaseModel):
    """Room Websocket incoming event."""

    event: Literal["message"]
    data: MessageIn


class RoomWebsocketOutMessage(BaseModel):
    """Room Websocket outgoing message event."""

    event: Literal["message"] = "message"
    data: Message


class RoomWebsocketOutEnterLeaveData(BaseModel):
    """Room Websocket outgoing enter/leave event data."""

    user_id: int
    users: list[int]
    time: datetime


class RoomWebsocketOutEnter(BaseModel):
    """Room Websocket outgoing enter event."""

    event: Literal["enter"] = "enter"
    data: RoomWebsocketOutEnterLeaveData


class RoomWebsocketOutLeave(BaseModel):
    """Room Websocket outgoing leave event."""

    event: Literal["leave"] = "leave"
    data: RoomWebsocketOutEnterLeaveData


RoomWebsocketOut = Annotated[
    RoomWebsocketOutEnter | RoomWebsocketOutLeave | RoomWebsocketOutMessage,
    pydantic.Field(discriminator="event"),
]


class RoomIn(BaseModel):
    """Room In schema."""

    name: str


class Room(RoomIn):
    """Room schema."""

    id: int
    created_by: int
    created_at: datetime


TodoStatus = Literal["todo", "in progress", "done"]


class TodoIn(BaseModel):
    """Todo item."""

    status: TodoStatus
    description: str


class Todo(TodoIn):
    """Todo item out."""

    id: int
    created_by: int
    created_at: datetime
    modified_at: datetime


class UserIn(BaseModel):
    """User create schema."""

    username: str
    email: str
    password: str


class User(BaseModel):
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


class File(BaseModel):
    """File."""

    fs_filename: str
    fs_folder: str
    filename: str
    content_type: str
    size: int
    checksum: str
    uploaded_at: datetime


class FileDB(File):
    """File in DB."""

    id: int
    user_id: int


class RoomUser(BaseModel):
    """Room User."""

    room_id: int
    user_id: int


class RoomUserDB(RoomUser):
    """Room User in DB."""

    id: int
