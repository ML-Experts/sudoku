from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from api.dependencies import get_preprocess_board_command_handler
from api.models.error_api_response import ErrorApiResponse
from api.models.image_api_entry import ImageApiEntry
from api.models.image_api_response import ImageApiResponse
from application.features.preprocessing.commands.preprocess_board.preprocess_board_command import (
    PreprocessBoardCommand,
)
from application.features.preprocessing.commands.preprocess_board.preprocess_board_command_handler import (
    PreprocessBoardCommandError,
    PreprocessBoardCommandHandler,
)

preprocessing_controller = APIRouter(prefix="/ml", tags=["preprocessing"])


@preprocessing_controller.put(
    "/preprocess/board",
    response_model=ImageApiResponse,
    responses={422: {"model": ErrorApiResponse}},
)
async def preprocess_board(
    image_entry: ImageApiEntry,
    command_handler: PreprocessBoardCommandHandler = Depends(
        get_preprocess_board_command_handler
    ),
) -> ImageApiResponse:
    command = PreprocessBoardCommand(
        mime_type=image_entry.mime_type,
        base64_image=image_entry.base64,
    )

    try:
        result = command_handler.handle(command)
    except PreprocessBoardCommandError as error:
        error_response = ErrorApiResponse(
            error_type=error.error_type,
            message=error.message,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=error_response.model_dump(by_alias=True),
        )

    return ImageApiResponse.from_dto(result)
