"""Files related routes."""

import fastapi
from fastapi import responses, status

from chatrooms import auth, file_upload, schemas
from chatrooms.database import DB, queries
from chatrooms.routers.commons import default_errors
from chatrooms.settings import Settings

router = fastapi.APIRouter(
    prefix="/files",
    tags=["files"],
    responses=default_errors(status.HTTP_401_UNAUTHORIZED),
    dependencies=[fastapi.Depends(auth.get_current_active_user)],
)


@router.get(
    "/avatars/{file_id}",
    responses=default_errors(status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND),
)
async def get_avatar(file_id: int, db: DB, settings: Settings) -> fastapi.Response:
    """Get avatar by file_id."""
    file: schemas.FileDB | None = await queries.select_file_by_id(db, id=file_id)

    if file is None or file.fs_folder != file_upload.Folders.avatars:
        raise fastapi.HTTPException(status.HTTP_404_NOT_FOUND)

    filepath = settings.fs_root / file.fs_folder / file.fs_filename

    return responses.FileResponse(
        path=filepath, filename=file.filename, media_type=file.content_type
    )
