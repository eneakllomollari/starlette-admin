from typing import Generator

import gridfs
from bson import ObjectId
from mongoengine.connection import get_db
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.routing import Route
from starlette_admin.base import BaseAdmin


class Admin(BaseAdmin):
    def mount_to(self, app: Starlette) -> None:
        self.routes.append(
            Route(
                "/api/file/{db}/{col}/{pk}",
                _serve_file,
                methods=["GET"],
                name="api:file",
            )
        )
        super().mount_to(app)


def _read_grid_out(grid_out: gridfs.grid_file.GridOut) -> Generator:
    while True:
        chunk = grid_out.read(
            255 * 1024
        )  # GridOut uses a default chunk size of 255 KB.
        if not chunk:
            break
        yield chunk


def _serve_file(request: Request) -> Response:
    pk = request.path_params.get("pk")
    col = request.path_params.get("col")
    db = request.path_params.get("db")
    fs = gridfs.GridFS(get_db(db), col)  # type: ignore
    try:
        file = fs.get(ObjectId(pk))
        return StreamingResponse(
            _read_grid_out(file),
            media_type=file.content_type,
            headers={"Content-Disposition": f"attachment;filename={file.filename}"},
        )
    except Exception:
        raise HTTPException(404)  # noqa B904
