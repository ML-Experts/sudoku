from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from api.dependencies import get_prepare_dataset_artifact_command_handler
from api.models.error_api_response import ErrorApiResponse
from api.models.prepare_dataset_artifact_api_entry import (
    PrepareDatasetArtifactApiEntry,
)
from api.models.prepared_dataset_artifact_api_response import (
    PreparedDatasetArtifactApiResponse,
)
from application.features.datasets.commands.prepare_dataset_artifact.prepare_dataset_artifact_command import (
    PrepareDatasetArtifactCommand,
)
from application.features.datasets.commands.prepare_dataset_artifact.prepare_dataset_artifact_command_handler import (
    PrepareDatasetArtifactCommandHandler,
)
from application.features.datasets.dto.dataset_split_policy_dto import (
    DatasetSplitPolicyDto,
    SplitRatiosDto,
)
from application.features.datasets.dto.prepare_dataset_source_dto import (
    PrepareDatasetSourceDto,
)
from application.features.datasets.errors.dataset_preparation_errors import (
    PrepareDatasetArtifactCommandError,
)

datasets_controller = APIRouter(prefix="/ml/datasets", tags=["datasets"])


def _unprocessable_content_response(
    error_type: str, message: str
) -> JSONResponse:
    error_response = ErrorApiResponse(error_type=error_type, message=message)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=error_response.model_dump(by_alias=True),
    )


def _internal_server_error_response(message: str) -> JSONResponse:
    error_response = ErrorApiResponse(
        error_type="internal_server_error",
        message=message,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(by_alias=True),
    )


@datasets_controller.post(
    "/prepare",
    response_model=PreparedDatasetArtifactApiResponse,
    responses={
        422: {"model": ErrorApiResponse},
        500: {"model": ErrorApiResponse},
    },
)
async def prepare_dataset_artifact(
    entry: PrepareDatasetArtifactApiEntry,
    command_handler: PrepareDatasetArtifactCommandHandler = Depends(
        get_prepare_dataset_artifact_command_handler
    ),
) -> PreparedDatasetArtifactApiResponse | JSONResponse:
    command = PrepareDatasetArtifactCommand(
        dataset_name=entry.dataset_name,
        preprocessing_profile=entry.preprocessing_profile,
        sources=tuple(
            PrepareDatasetSourceDto(
                name=source.name,
                type=source.type,
                split_policy=DatasetSplitPolicyDto(
                    mode=source.split_policy.mode,
                    group_by=source.split_policy.group_by,
                    ratios=SplitRatiosDto(
                        train=source.split_policy.ratios.train,
                        val=source.split_policy.ratios.val,
                        test=source.split_policy.ratios.test,
                    ),
                ),
            )
            for source in entry.sources
        ),
    )

    try:
        result = command_handler.handle(command)
    except PrepareDatasetArtifactCommandError as error:
        return _unprocessable_content_response(
            error_type=error.error_type,
            message=error.message,
        )
    except Exception:
        return _internal_server_error_response(
            message="Wystąpił nieobsłużony błąd przygotowania datasetu."
        )

    return PreparedDatasetArtifactApiResponse.from_dto(result)
