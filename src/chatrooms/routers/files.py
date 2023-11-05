"""Files related routes."""

from os import path

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.responses import FileResponse, Response

from chatrooms import auth, database
from chatrooms.database.connections import DB
from chatrooms.routers.commons import default_errors
from chatrooms.settings import Settings

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses=default_errors(401),
    dependencies=[Depends(auth.get_current_active_user)],
)


@router.get("/avatars/{file_id}", responses=default_errors(401, 404))
async def get_avatar(file_id: int, db: DB, settings: Settings) -> Response:
    """Get avatar by file_id."""
    file = await database.files.get_file_by_id(db=db, file_id=file_id)
    if file is None or not file.fs_filename.startswith("avatars/"):
        raise HTTPException(404)
    filepath = path.join(settings.fs_root, file.fs_filename)
    return FileResponse(path=filepath, filename=file.filename, media_type=file.content_type)
