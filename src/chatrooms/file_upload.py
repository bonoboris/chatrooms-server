"""File upload helpers."""

import hashlib
from collections import abc
from datetime import datetime
from os import path
from random import randbytes
from typing import Annotated

from fastapi import BackgroundTasks, Depends, HTTPException, UploadFile

from chatrooms.auth import ActiveUser
from chatrooms.routers.commons import utcnow
from chatrooms.schemas import File
from chatrooms.settings import Settings

IMAGE_TYPES = (
    "image/jpeg",
    "image/png",
    "image/svg+xml",
    "image/webp",
)


def format_octets(size: int) -> str:
    """Format octets to human readable string."""
    siz = float(size)
    for unit in ("o", "ko", "Mo", "Go", "To"):
        if siz < 1024:  # noqa: PLR2004
            return f"{round(siz)} {unit}"
        siz /= 1024
    return f"{round(siz)} Po"


async def validate_file(
    file: UploadFile, max_size: int = 0, allowed_types: str | abc.Collection[str] | None = None
) -> tuple[bytes, str, str]:
    """Validate file, raise error if doesn't match constraints.

    Returns data as bytes, filename & filetype.
    """
    data = await file.read()
    size = len(data)
    content_type = file.content_type
    filename = file.filename

    if max_size > 0 and size > max_size:
        raise HTTPException(400, f"File size exceed limit: {format_octets(max_size)}")
    if content_type is None:
        raise HTTPException(400, "Missing file content type")
    if filename is None:
        raise HTTPException(400, "Missing file name")
    if allowed_types is not None:
        if isinstance(allowed_types, str) and file.content_type != allowed_types:
            raise HTTPException(400, f"Invalid file content type, expected: {allowed_types}")
        if content_type not in allowed_types:
            raise HTTPException(400, f"Invalid file content type, expected on of: {allowed_types}")
    return data, filename, content_type


def generate_filename(folder: str, uploaded_at: datetime, checksum: str) -> str:
    """Generate a filepath from folder, upload_at and checksum."""
    return f"{folder}/{int(uploaded_at.timestamp())}_{randbytes(4).hex()}_{checksum[:16]}"


def write_on_filesystem(filepath: str, data: bytes) -> None:
    """Write data on filesystem."""
    with open(filepath, "wb") as file:
        file.write(data)


class FileWriterClass:
    """Write a file on the filesystem as a backgroud task."""

    def __init__(
        self, settings: Settings, user: ActiveUser, background_tasks: BackgroundTasks
    ) -> None:
        self.settings = settings
        self.user = user
        self.background_tasks = background_tasks

    def __call__(self, folder: str, data: bytes, filename: str, content_type: str) -> File:
        """Write file on filesystem as backgroud task and return File instance."""
        size = len(data)
        checksum = hashlib.sha256(data).hexdigest()
        uploadad_at = utcnow()
        fs_filename = generate_filename(folder=folder, checksum=checksum, uploaded_at=uploadad_at)
        fs_path = path.join(self.settings.fs_root, fs_filename)
        self.background_tasks.add_task(write_on_filesystem, fs_path, data)
        return File(
            fs_filename=fs_filename,
            filename=filename,
            checksum=checksum,
            content_type=content_type,
            size=size,
            uploaded_at=uploadad_at,
        )


FileWriter = Annotated[FileWriterClass, Depends(FileWriterClass)]


class UpdloadFilePolicy:
    """Perform checks on uploaded file and write it on the filesystem as a backgroud task."""

    def __init__(
        self, folder: str, max_size: int = 0, allowed_types: str | abc.Sequence[str] = "*"
    ) -> None:
        self.max_size = max_size
        self.allowed_types = allowed_types
        self.folder = folder

    async def __call__(self, upload_file: UploadFile, file_writer: FileWriter) -> File:
        """Validate file, write on filesystem, and return `File` instance.

        Raise error if doesn't match constraints.
        """
        data, filename, content_type = await validate_file(
            upload_file, self.max_size, self.allowed_types
        )
        return file_writer(self.folder, data, filename, content_type)
