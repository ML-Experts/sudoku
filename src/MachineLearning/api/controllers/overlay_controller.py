import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from api.dependencies import get_render_overlay_cell_command_handler
from api.models.error_api_response import ErrorApiResponse
from api.models.image_api_response import ImageApiResponse
from api.models.render_sudoku_overlay_cell_api_entry import (
    RenderSudokuOverlayCellApiEntry,
)
from application.features.overlay.commands.render_overlay_cell.render_overlay_cell_command import (
    RenderOverlayCellCommand,
)
from application.features.overlay.commands.render_overlay_cell.render_overlay_cell_command_handler import (
    RenderOverlayCellCommandHandler,
)
from application.features.overlay.errors.render_overlay_cell_errors import (
    RenderOverlayCellCommandError,
)

_logger = logging.getLogger(__name__)

overlay_controller = APIRouter(
    prefix="/ml/sudoku/overlay",
    tags=["overlay"],
)


@overlay_controller.post(
    "/cells",
    response_model=ImageApiResponse,
    responses={
        422: {"model": ErrorApiResponse},
        500: {"model": ErrorApiResponse},
    },
)
async def render_overlay_cell(
    entry: RenderSudokuOverlayCellApiEntry,
    command_handler: RenderOverlayCellCommandHandler = Depends(
        get_render_overlay_cell_command_handler
    ),
) -> ImageApiResponse | JSONResponse:
    command = RenderOverlayCellCommand(
        mime_type=entry.cell_image.mime_type,
        base64_image=entry.cell_image.base64,
        digit=entry.digit,
        row_index=entry.row_index,
        column_index=entry.column_index,
    )

    try:
        result = command_handler.handle(command)
    except RenderOverlayCellCommandError as error:
        return _error_response(
            status_code=error.status_code,
            error_type=error.error_type,
            message=error.message,
        )
    except Exception:
        _logger.exception("Unhandled error while rendering overlay cell.")
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="internal_server_error",
            message="Wystąpił nieobsłużony błąd renderowania overlay komórki.",
        )

    return ImageApiResponse(
        mime_type=result.mime_type,
        base64=result.base64,
    )


def _error_response(
    status_code: int,
    error_type: str,
    message: str,
) -> JSONResponse:
    error_response = ErrorApiResponse(error_type=error_type, message=message)
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(by_alias=True),
    )
