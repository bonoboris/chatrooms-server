"""Todos related routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from chatrooms import auth, database, schemas
from chatrooms.database.connections import DB
from chatrooms.routers.commons import DeleteStatus, Pagination, default_errors, utcnow

router = APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses=default_errors(401),
    dependencies=[Depends(auth.get_current_active_user)],
)


@router.get("/")
async def get_all_todos(db: DB, user: auth.ActiveUser, page: Pagination) -> list[schemas.Todo]:
    """Get all todos."""
    return await database.todos.get_todos_by_created_by(
        db=db, created_by=user.id, **page.model_dump()
    )


@router.post("/", status_code=status.HTTP_201_CREATED, responses=default_errors(401))
async def create_todo(db: DB, user: auth.ActiveUser, data: schemas.TodoIn) -> schemas.Todo:
    """Create a new todo."""
    now = utcnow()
    return await database.todos.create_todo(
        db=db, todo=data, created_by=user.id, created_at=now, modified_at=now
    )


@router.get("/{todo_id}", responses=default_errors(403, 404))
async def get_one_todo(db: DB, user: auth.ActiveUser, todo_id: int) -> schemas.Todo:
    """Get todo by id."""
    todo = await database.todos.get_todo_by_id(db=db, todo_id=todo_id)
    if todo is None:
        raise HTTPException(404, detail=f"No todo found with id: {todo_id}")
    if todo.created_by != user.id:
        raise HTTPException(403)
    return todo


@router.put("/{todo_id}", responses=default_errors(403, 404))
async def update_todo(
    db: DB, user: auth.ActiveUser, todo_id: int, data: schemas.TodoIn
) -> schemas.Todo:
    """Update a todos."""
    todo = await database.todos.get_todo_by_id(db, todo_id=todo_id)
    if todo is None:
        raise HTTPException(404)
    if todo.created_by != user.id:
        raise HTTPException(403)
    return await database.todos.update_todo(db, todo_id, data, modified_at=utcnow())


@router.delete("/{todo_id}", responses=default_errors(403, 404))
async def delete_todo(db: DB, user: auth.ActiveUser, todo_id: int) -> DeleteStatus:
    """Delete a todo."""
    todo = await database.todos.get_todo_by_id(db, todo_id=todo_id)
    if todo is None:
        raise HTTPException(404)
    if todo.created_by != user.id:
        raise HTTPException(403)
    deleted = await database.todos.delete_todo(db, todo_id)
    if deleted:
        return DeleteStatus(status="deleted")
    return DeleteStatus(status="not found")
