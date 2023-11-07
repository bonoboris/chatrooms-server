"""All database queries."""
import datetime
import functools
from collections.abc import Awaitable, Callable
from typing import Concatenate, ParamSpec, TypeVar

from psycopg import AsyncCursor

from chatrooms import schemas
from chatrooms.database.connections import DB

_PT = ParamSpec("_PT")
_RT = TypeVar("_RT")
_TModel = TypeVar("_TModel", bound=schemas.BaseModel)


def cursor_or_db(
    model: type[_TModel]
) -> Callable[
    [Callable[Concatenate[AsyncCursor[_TModel], _PT], Awaitable[_RT]]],
    Callable[Concatenate[DB | AsyncCursor[_TModel], _PT], Awaitable[_RT]],
]:
    """Decorator to use cursor or db as first argument to database query functions.

    If the first argument is a cursor, then it will be used as is.
    If the first argument is a db, then it will be used to create a cursor.
    """

    def decorator(
        func: Callable[Concatenate[AsyncCursor[_TModel], _PT], Awaitable[_RT]]
    ) -> Callable[Concatenate[DB | AsyncCursor[_TModel], _PT], Awaitable[_RT]]:
        @functools.wraps(func)
        async def wrapper(
            db_or_cursor: DB | AsyncCursor[_TModel], *args: _PT.args, **kwargs: _PT.kwargs
        ) -> _RT:
            if isinstance(db_or_cursor, AsyncCursor):
                return await func(db_or_cursor, *args, **kwargs)

            async with db_or_cursor.cursor(row_factory=model.get_row_factory()) as cursor:
                return await func(cursor, *args, **kwargs)

        return wrapper

    return decorator


@cursor_or_db(schemas.UserDB)
async def select_user_by_id(cursor: AsyncCursor[schemas.UserDB], id: int) -> schemas.UserDB | None:
    """Select user by id."""
    await cursor.execute(
        """SELECT * FROM users WHERE id = %(id)s""",
        {"id": id},
    )
    return await cursor.fetchone()


@cursor_or_db(schemas.UserDB)
async def select_user_by_username(
    cursor: AsyncCursor[schemas.UserDB], username: str
) -> schemas.UserDB | None:
    """Select user by username."""
    await cursor.execute(
        """SELECT * FROM users WHERE username = %(username)s""",
        {"username": username},
    )
    return await cursor.fetchone()


@cursor_or_db(schemas.UserDB)
async def update_user_avatar_id_by_id(
    cursor: AsyncCursor[schemas.UserDB], id: int, avatar_id: int
) -> schemas.UserDB | None:
    """Update user avatar_id field by id."""
    await cursor.execute(
        """
        UPDATE users
        SET avatar_id = %(avatar_id)s
        WHERE id = %(id)s
        """,
        {"id": id, "avatar_id": avatar_id},
    )
    return await cursor.fetchone()


@cursor_or_db(schemas.FileDB)
async def select_file_by_id(cursor: AsyncCursor[schemas.FileDB], id: int) -> schemas.FileDB | None:
    """Select file by id."""
    await cursor.execute(
        """SELECT * FROM files WHERE id = %(id)s""",
        {"id": id},
    )
    return await cursor.fetchone()


@cursor_or_db(schemas.FileDB)
async def insert_file(  # noqa: PLR0913
    cursor: AsyncCursor[schemas.FileDB],
    fs_folder: str,
    fs_filename: str,
    filename: str,
    content_type: str,
    size: int,
    checksum: str,
    uploaded_at: datetime.datetime,
    user_id: int,
) -> schemas.FileDB:
    """Insert a file."""
    await cursor.execute(
        """
        INSERT INTO files(
            fs_filename,
            fs_folder,
            filename,
            content_type,
            size,
            checksum,
            uploaded_at,
            user_id
        )
        VALUES (
            %(fs_filename)s,
            %(fs_folder)s,
            %(filename)s,
            %(content_type)s,
            %(size)s,
            %(checksum)s,
            %(uploaded_at)s,
            %(user_id)s
        )
        RETURNING *
        """,
        {
            "fs_folder": fs_folder,
            "fs_filename": fs_filename,
            "filename": filename,
            "content_type": content_type,
            "size": size,
            "checksum": checksum,
            "uploaded_at": uploaded_at,
            "user_id": user_id,
        },
    )
    file = await cursor.fetchone()
    assert file is not None
    return file


@cursor_or_db(schemas.Message)
async def select_all_messages(
    cursor: AsyncCursor[schemas.Message], limit: int, offset: int
) -> list[schemas.Message]:
    """Select all messages."""
    await cursor.execute(
        """SELECT * FROM messages LIMIT %(limit)s OFFSET %(offset)s""",
        {"limit": limit, "offset": offset},
    )
    return await cursor.fetchall()


@cursor_or_db(schemas.Message)
async def select_all_messages_by_room_id(
    cursor: AsyncCursor[schemas.Message], room_id: int, limit: int, offset: int
) -> list[schemas.Message]:
    """Select all messages by room_id."""
    await cursor.execute(
        """
        SELECT * FROM messages
        WHERE room_id = %(room_id)s
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        {"room_id": room_id, "limit": limit, "offset": offset},
    )
    return await cursor.fetchall()


@cursor_or_db(schemas.Message)
async def insert_message(
    cursor: AsyncCursor[schemas.Message],
    content: str,
    room_id: int,
    created_by: int,
    created_at: datetime.datetime,
) -> schemas.Message:
    """Insert a message."""
    await cursor.execute(
        """
        INSERT INTO messages(content, room_id, created_by, created_at)
        VALUES (%(content)s, %(room_id)s, %(created_by)s, %(created_at)s)
        RETURNING *
        """,
        {
            "content": content,
            "room_id": room_id,
            "created_by": created_by,
            "created_at": created_at,
        },
    )
    message = await cursor.fetchone()
    assert message is not None
    return message


@cursor_or_db(schemas.Room)
async def select_all_rooms(
    cursor: AsyncCursor[schemas.Room], limit: int, offset: int
) -> list[schemas.Room]:
    """Select all rooms."""
    await cursor.execute(
        """SELECT * FROM rooms LIMIT %(limit)s OFFSET %(offset)s""",
        {"limit": limit, "offset": offset},
    )
    return await cursor.fetchall()


@cursor_or_db(schemas.Room)
async def insert_room(
    cursor: AsyncCursor[schemas.Room], name: str, created_by: int, created_at: datetime.datetime
) -> schemas.Room:
    """Insert a room."""
    await cursor.execute(
        """
        INSERT INTO rooms(name, created_by, created_at)
        VALUES (%(name)s, %(created_by)s, %(created_at)s)
        RETURNING *
        """,
        {"name": name, "created_by": created_by, "created_at": created_at},
    )
    room = await cursor.fetchone()
    assert room is not None
    return room


@cursor_or_db(schemas.Room)
async def select_room_by_id(cursor: AsyncCursor[schemas.Room], id: int) -> schemas.Room | None:
    """Select room by id."""
    await cursor.execute(
        """SELECT * FROM rooms WHERE id = %(id)s""",
        {"id": id},
    )
    return await cursor.fetchone()


@cursor_or_db(schemas.Todo)
async def select_all_todos_by_user_id(
    cursor: AsyncCursor[schemas.Todo], user_id: int, limit: int, offset: int
) -> list[schemas.Todo]:
    """Select all todos by user_id."""
    await cursor.execute(
        """
        SELECT * FROM todos
        WHERE created_by = %(created_by)s
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        {"created_by": user_id, "limit": limit, "offset": offset},
    )
    return await cursor.fetchall()


@cursor_or_db(schemas.Todo)
async def insert_todo(
    cursor: AsyncCursor[schemas.Todo],
    status: str,
    description: str,
    created_by: int,
    created_at: datetime.datetime,
    modified_at: datetime.datetime,
) -> schemas.Todo:
    """Insert a todo."""
    await cursor.execute(
        """
        INSERT INTO todos(status, description, created_by, created_at, modified_at)
        VALUES (%(status)s, %(description)s, %(created_by)s, %(created_at)s, %(modified_at)s)
        RETURNING *
        """,
        {
            "status": status,
            "description": description,
            "created_by": created_by,
            "created_at": created_at,
            "modified_at": modified_at,
        },
    )
    todo = await cursor.fetchone()
    assert todo is not None
    return todo


@cursor_or_db(schemas.Todo)
async def select_todo_by_id(cursor: AsyncCursor[schemas.Todo], id: int) -> schemas.Todo | None:
    """Select todo by id."""
    await cursor.execute(
        """SELECT * FROM todos WHERE id = %(id)s""",
        {"id": id},
    )
    return await cursor.fetchone()


@cursor_or_db(schemas.Todo)
async def update_todo_by_id(
    cursor: AsyncCursor[schemas.Todo],
    id: int,
    status: str,
    description: str,
    modified_at: datetime.datetime,
) -> schemas.Todo | None:
    """Update todo by id."""
    await cursor.execute(
        """
        UPDATE todos
        SET status = %(status)s, description = %(description)s, modified_at = %(modified_at)s
        WHERE id = %(id)s
        RETURNING *
        """,
        {
            "id": id,
            "status": status,
            "description": description,
            "modified_at": modified_at,
        },
    )
    return await cursor.fetchone()


@cursor_or_db(schemas.Todo)
async def delete_todo_by_id(cursor: AsyncCursor[schemas.Todo], id: int) -> bool:
    """Delete todo by id."""
    await cursor.execute(
        """DELETE FROM todos WHERE id = %(id)s""",
        {"id": id},
    )
    return cursor.rowcount > 0
