"""Users related routes."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends

from chatrooms import auth, database, file_upload, schemas
from chatrooms import avatar as m_avatar
from chatrooms.database.connections import DB
from chatrooms.routers.commons import default_errors

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses=default_errors(401),
    dependencies=[Depends(auth.get_current_active_user)],
)


@router.get("/current")
async def get_current_user(user: auth.ActiveUser) -> schemas.UserFull:
    """Get logged-in user."""
    return user


@router.get("/{user_id}")
async def get_user(db: DB, user_id: int) -> schemas.User:
    """Get user by id."""
    user = await database.users.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(404)
    return user


AvatarUploadPolicy = file_upload.UpdloadFilePolicy(
    folder="avatars", max_size=2**20, allowed_types=file_upload.IMAGE_TYPES
)
AvatarFile = Annotated[schemas.File, Depends(AvatarUploadPolicy)]


@router.post("/current/avatar", status_code=status.HTTP_202_ACCEPTED)
async def upload_avatar(db: DB, file: AvatarFile, user: auth.ActiveUser) -> schemas.UserFull:
    """Update user avatar, return updated user."""
    avatar = await database.files.create_file(db, file, user_id=user.id)
    return await database.users.update_user_avatar(db, user_id=user.id, avatar_id=avatar.id)


@router.post("/current/generate_avatar", status_code=status.HTTP_202_ACCEPTED)
async def generate_avatar(
    db: DB, user: auth.ActiveUser, file_writer: file_upload.FileWriter
) -> schemas.UserFull:
    """Update user avatar, return updated user."""
    data = m_avatar.generate_avatar(title=f"{user.username} avatar").encode("utf8")
    file = file_writer(
        folder="avatars",
        data=data,
        filename=f"{user.username} avatar.svg",
        content_type="image/svg+xml",
    )
    avatar = await database.files.create_file(db, file, user_id=user.id)
    return await database.users.update_user_avatar(db, user_id=user.id, avatar_id=avatar.id)
