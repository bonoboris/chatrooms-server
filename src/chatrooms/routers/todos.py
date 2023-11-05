"""Todos related routes."""

import fastapi
from fastapi import status

from chatrooms import auth, schemas
from chatrooms.database import DB, queries
from chatrooms.routers.commons import DeleteStatus, Pagination, default_errors, utcnow

router = fastapi.APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses=default_errors(status.HTTP_401_UNAUTHORIZED),
    dependencies=[fastapi.Depends(auth.get_current_active_user)],
)


@router.get("/")
async def get_all_todos(db: DB, user: auth.ActiveUser, page: Pagination) -> list[schemas.Todo]:
    """Get all todos owned by the user."""
    return await queries.select_all_todos_by_user_id(
        db, user_id=user.id, limit=page.limit, offset=page.skip
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(db: DB, user: auth.ActiveUser, data: schemas.TodoIn) -> schemas.Todo:
    """Create a new todo."""
    now = utcnow()
    return await queries.insert_todo(
        db,
        status=data.status,
        description=data.description,
        created_by=user.id,
        created_at=now,
        modified_at=now,
    )


@router.get(
    "/{todo_id}", responses=default_errors(status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)
)
async def get_one_todo(db: DB, user: auth.ActiveUser, todo_id: int) -> schemas.Todo:
    """Get todo by id."""
    todo = await queries.select_todo_by_id(db, id=todo_id)
    if todo is None:
        raise fastapi.HTTPException(status.HTTP_404_NOT_FOUND)
    if todo.created_by != user.id:
        raise fastapi.HTTPException(status.HTTP_403_FORBIDDEN)
    return todo


@router.put(
    "/{todo_id}", responses=default_errors(status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)
)
async def update_todo(
    db: DB, user: auth.ActiveUser, todo_id: int, data: schemas.TodoIn
) -> schemas.Todo:
    """Update a todos."""
    async with db.cursor(row_factory=schemas.Todo.get_row_factory()) as cursor:
        todo = await queries.select_todo_by_id(cursor, id=todo_id)
        if todo is None:
            raise fastapi.HTTPException(status.HTTP_404_NOT_FOUND)
        if todo.created_by != user.id:
            raise fastapi.HTTPException(status.HTTP_403_FORBIDDEN)
        todo = await queries.update_todo_by_id(
            cursor,
            id=todo_id,
            status=data.status,
            description=data.description,
            modified_at=utcnow(),
        )
        if todo is None:
            raise fastapi.HTTPException(status.HTTP_404_NOT_FOUND)
        return todo


@router.delete(
    "/{todo_id}", responses=default_errors(status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)
)
async def delete_todo(db: DB, user: auth.ActiveUser, todo_id: int) -> DeleteStatus:
    """Delete a todo."""
    async with db.cursor(row_factory=schemas.Todo.get_row_factory()) as cursor:
        todo = await queries.select_todo_by_id(cursor, id=todo_id)
        if todo is None:
            raise fastapi.HTTPException(status.HTTP_404_NOT_FOUND)
        if todo.created_by != user.id:
            raise fastapi.HTTPException(status.HTTP_403_FORBIDDEN)
        if await queries.delete_todo_by_id(cursor, id=todo_id):
            return DeleteStatus(status="deleted")
        return DeleteStatus(status="not found")
