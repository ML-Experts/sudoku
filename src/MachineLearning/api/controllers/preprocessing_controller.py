from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from api.dependencies import (
    get_extract_cells_command_handler,
    get_preprocess_board_command_handler,
)
from api.models.cells_grid_api_response import CellsGridApiResponse
from api.models.error_api_response import ErrorApiResponse
from api.models.image_api_entry import ImageApiEntry
from api.models.image_api_response import ImageApiResponse
from application.features.preprocessing.commands.extract_cells.extract_cells_command import (
    ExtractCellsCommand,
)
from application.features.preprocessing.commands.extract_cells.extract_cells_command_handler import (
    ExtractCellsCommandError,
    ExtractCellsCommandHandler,
)
from application.features.preprocessing.commands.preprocess_board.preprocess_board_command import (
    PreprocessBoardCommand,
)
from application.features.preprocessing.commands.preprocess_board.preprocess_board_command_handler import (
    PreprocessBoardCommandError,
    PreprocessBoardCommandHandler,
)

preprocessing_controller = APIRouter(prefix="/ml", tags=["preprocessing"])


def _unprocessable_content_response(
    error_type: str, message: str
) -> JSONResponse:
    error_response = ErrorApiResponse(error_type=error_type, message=message)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=error_response.model_dump(by_alias=True),
    )


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
        return _unprocessable_content_response(
            error_type=error.error_type,
            message=error.message,
        )

    return ImageApiResponse.from_dto(result)


@preprocessing_controller.put(
    "/preprocess/cells",
    response_model=CellsGridApiResponse,
    responses={422: {"model": ErrorApiResponse}},
)
async def preprocess_cells(
    image_entry: ImageApiEntry,
    command_handler: ExtractCellsCommandHandler = Depends(
        get_extract_cells_command_handler
    ),
) -> CellsGridApiResponse:
    command = ExtractCellsCommand(
        mime_type=image_entry.mime_type,
        base64_image=image_entry.base64,
    )

    try:
        result = command_handler.handle(command)
    except ExtractCellsCommandError as error:
        return _unprocessable_content_response(
            error_type=error.error_type,
            message=error.message,
        )

    return CellsGridApiResponse.from_dto(result)

@preprocessing_controller.put(
    "/preprocess/binarize",
    response_model=ImageApiResponse,
    responses={422: {"model": ErrorApiResponse}},
)
async def preprocess_binarize(
    image_entry: ImageApiEntry,
    command_handler: PreprocessBoardCommandHandler = Depends(
        get_preprocess_board_command_handler
    ),
) -> ImageApiResponse:
    try:
        encoded_input_image = command_handler._image_codec.decode_base64_image(
            base64_image=image_entry.base64,
            mime_type=image_entry.mime_type,
        )

        source_image = command_handler._image_codec.decode_image(
            encoded_input_image
        )

        binary_image = command_handler._adaptive_threshold_binarizer.binarize(
            source_image
        )

        encoded_output_image = command_handler._image_codec.encode_image(
            binary_image, command_handler._output_mime_type
        )

        output_base64 = command_handler._image_codec.encode_to_base64(
            encoded_output_image
        )

    except ValueError as error:
        return _unprocessable_content_response(
            error_type="invalid_image_payload",
            message="invalid_image_payload",
        )

    return ImageApiResponse(
        mime_type=command_handler._output_mime_type,
        base64=output_base64,
    )
