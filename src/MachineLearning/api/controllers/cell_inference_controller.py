from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from api.dependencies import get_infer_cell_digit_command_handler
from api.models.cell_digit_inference_api_entry import CellDigitInferenceApiEntry
from api.models.cell_digit_inference_api_response import (
    CellDigitInferenceApiResponse,
)
from api.models.error_api_response import ErrorApiResponse
from application.features.inference.commands.infer_cell_digit.infer_cell_digit_command import (
    InferCellDigitCommand,
)
from application.features.inference.dto.inference_runtime_configuration_dto import (
    InferenceRuntimeConfigurationDto,
)
from application.features.inference.dto.inference_runtime_model_reference_dto import (
    InferenceRuntimeModelReferenceDto,
)
from application.features.inference.errors.cell_digit_inference_errors import (
    CellDigitInferenceCommandError,
)

if TYPE_CHECKING:
    from application.features.inference.commands.infer_cell_digit.infer_cell_digit_command_handler import (
        InferCellDigitCommandHandler,
    )

LOGGER = logging.getLogger(__name__)

cell_inference_controller = APIRouter(
    prefix="/ml/cells",
    tags=["cell-inference"],
)


@cell_inference_controller.put(
    "/inference",
    response_model=CellDigitInferenceApiResponse,
    responses={
        422: {"model": ErrorApiResponse},
        500: {"model": ErrorApiResponse},
    },
)
async def infer_cell_digit(
    entry: CellDigitInferenceApiEntry,
    command_handler: InferCellDigitCommandHandler = Depends(
        get_infer_cell_digit_command_handler
    ),
) -> CellDigitInferenceApiResponse | JSONResponse:
    command = InferCellDigitCommand(
        mime_type=entry.image.mime_type,
        base64_image=entry.image.base64,
        active_model=InferenceRuntimeModelReferenceDto(
            name=entry.active_model.name,
            manifest_path=entry.active_model.manifest_path,
            primary_artifact_path=entry.active_model.primary_artifact_path,
            input_profile=entry.active_model.input_profile,
        ),
        resolved_configuration=InferenceRuntimeConfigurationDto(
            inference_profile_name=
                entry.resolved_configuration.inference_profile_name,
            empty_cell_inner_margin_ratio=
                entry.resolved_configuration.empty_cell_inner_margin_ratio,
            empty_cell_dark_pixel_ratio_threshold=
                entry.resolved_configuration.empty_cell_dark_pixel_ratio_threshold,
            center_area_ratio=entry.resolved_configuration.center_area_ratio,
            min_component_area_ratio=entry.resolved_configuration.min_component_area_ratio,
            line_artifact_min_span_ratio=entry.resolved_configuration.line_artifact_min_span_ratio,
            line_artifact_max_thickness_ratio=entry.resolved_configuration.line_artifact_max_thickness_ratio
        ),
    )

    try:
        result = command_handler.handle(command)
    except CellDigitInferenceCommandError as error:
        LOGGER.warning(
            "Cell inference request rejected: status=%s error_type=%s message=%s "
            "mime_type=%s active_model=%s input_profile=%s inference_profile=%s "
            "image_base64_length=%s",
            error.status_code,
            error.error_type,
            error.message,
            entry.image.mime_type,
            entry.active_model.name,
            entry.active_model.input_profile,
            entry.resolved_configuration.inference_profile_name,
            len(entry.image.base64),
        )
        return _error_response(
            status_code=error.status_code,
            error_type=error.error_type,
            message=error.message,
        )
    except Exception:
        LOGGER.exception(
            "Cell inference request failed unexpectedly: mime_type=%s "
            "active_model=%s input_profile=%s inference_profile=%s "
            "image_base64_length=%s",
            entry.image.mime_type,
            entry.active_model.name,
            entry.active_model.input_profile,
            entry.resolved_configuration.inference_profile_name,
            len(entry.image.base64),
        )
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="internal_server_error",
            message="Wystąpił nieobsłużony błąd inferencji komórki.",
        )

    return CellDigitInferenceApiResponse.from_dto(result)


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
