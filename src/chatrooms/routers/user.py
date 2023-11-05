"""Users related routes."""

from typing import Annotated

import fastapi
from fastapi import status

from chatrooms import auth, file_upload, schemas
from chatrooms import avatar as m_avatar
from chatrooms.database import DB, queries
from chatrooms.routers.commons import default_errors

router = fastapi.APIRouter(
    prefix="/users",
    tags=["users"],
    responses=default_errors(status.HTTP_401_UNAUTHORIZED),
    dependencies=[fastapi.Depends(auth.get_current_active_user)],
)


@router.get("/current")
async def get_current_user(user: auth.ActiveUser) -> schemas.UserFull:
    """Get logged-in user."""
    return user


@router.get("/{user_id}")
async def get_user(db: DB, user_id: int) -> schemas.User:
    """Get user by id."""
    user = await queries.select_user_by_id(db, id=user_id)
    if user is None:
        raise fastapi.HTTPException(status.HTTP_404_NOT_FOUND)
    return user


AvatarUploadPolicy = file_upload.UpdloadFilePolicy(
    folder="avatars", max_size=2**20, allowed_types=file_upload.IMAGE_TYPES
)
AvatarFile = Annotated[schemas.File, fastapi.Depends(AvatarUploadPolicy)]
"""Perform checks on uploaded avatar file and write it on the filesystem as a backgroud task."""


@router.post("/current/avatar", status_code=status.HTTP_202_ACCEPTED)
async def upload_avatar(db: DB, file: AvatarFile, user: auth.ActiveUser) -> schemas.UserFull:
    """Update user avatar, return updated user."""
    avatar = await queries.insert_file(
        db,
        fs_filename=file.fs_filename,
        filename=file.filename,
        content_type=file.content_type,
        size=file.size,
        checksum=file.checksum,
        uploaded_at=file.uploaded_at,
        user_id=user.id,
    )
    user_db = await queries.update_user_avatar_id_by_id(db, id=user.id, avatar_id=avatar.id)
    if user_db is None:
        raise fastapi.HTTPException(status.HTTP_404_NOT_FOUND)
    return user_db


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
    avatar = await queries.insert_file(
        db,
        fs_filename=file.fs_filename,
        filename=file.filename,
        content_type=file.content_type,
        size=file.size,
        checksum=file.checksum,
        uploaded_at=file.uploaded_at,
        user_id=user.id,
    )
    user_db = await queries.update_user_avatar_id_by_id(db, id=user.id, avatar_id=avatar.id)
    if user_db is None:
        raise fastapi.HTTPException(status.HTTP_404_NOT_FOUND)
    return user_db
