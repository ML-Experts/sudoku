import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from api.dependencies import (
    get_create_dataset_preparation_command_handler,
    get_prepare_dataset_artifact_command_handler,
)
from api.models.create_dataset_preparation_api_entry import (
    CreateDatasetPreparationApiEntry,
)
from api.models.create_dataset_preparation_api_response import (
    CreateDatasetPreparationApiResponse,
)
from api.models.error_api_response import ErrorApiResponse
from api.models.prepare_dataset_artifact_api_entry import (
    PrepareDatasetArtifactApiEntry,
)
from api.models.prepared_dataset_artifact_api_response import (
    PreparedDatasetArtifactApiResponse,
)
from application.features.datasets.commands.create_dataset_preparation.create_dataset_preparation_command import (
    CreateDatasetPreparationCommand,
)
from application.features.datasets.commands.create_dataset_preparation.create_dataset_preparation_command_handler import (
    CreateDatasetPreparationCommandHandler,
)
from application.features.datasets.commands.prepare_dataset_artifact.prepare_dataset_artifact_command import (
    PrepareDatasetArtifactCommand,
)
from application.features.datasets.commands.prepare_dataset_artifact.prepare_dataset_artifact_command_handler import (
    PrepareDatasetArtifactCommandHandler,
)
from application.features.datasets.dto.create_dataset_preparation_source_dto import (
    CreateDatasetPreparationSourceDto,
)
from application.features.datasets.dto.dataset_split_policy_dto import (
    DatasetSplitPolicyDto,
    SplitRatiosDto,
)
from application.features.datasets.dto.prepare_dataset_source_dto import (
    PrepareDatasetSourceDto,
)
from application.features.datasets.errors.dataset_preparation_errors import (
    CreateDatasetPreparationCommandError,
    PrepareDatasetArtifactCommandError,
)

datasets_controller = APIRouter(prefix="/ml/datasets", tags=["datasets"])
LOGGER = logging.getLogger(__name__)


def _unprocessable_content_response(
    error_type: str, message: str
) -> JSONResponse:
    error_response = ErrorApiResponse(error_type=error_type, message=message)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=error_response.model_dump(by_alias=True),
    )


def _internal_server_error_response(message: str) -> JSONResponse:
    return _server_error_response(
        error_type="internal_server_error",
        message=message,
    )


def _server_error_response(error_type: str, message: str) -> JSONResponse:
    error_response = ErrorApiResponse(
        error_type=error_type,
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
    LOGGER.info(
        "Received dataset prepare request: preparation=%s dataset=%s source_count=%s",
        entry.preparation_name,
        entry.dataset_name,
        len(entry.sources),
    )
    command = PrepareDatasetArtifactCommand(
        preparation_name=entry.preparation_name,
        dataset_name=entry.dataset_name,
        split_policy=DatasetSplitPolicyDto(
            mode=entry.split_policy.mode,
            group_by=entry.split_policy.group_by,
            ratios=SplitRatiosDto(
                train=entry.split_policy.ratios.train,
                val=entry.split_policy.ratios.val,
                test=entry.split_policy.ratios.test,
            ),
        ),
        sources=tuple(
            PrepareDatasetSourceDto(
                name=source.name,
                type=source.type,
                splits=tuple(source.splits),
            )
            for source in entry.sources
        ),
    )

    try:
        result = command_handler.handle(command)
    except PrepareDatasetArtifactCommandError as error:
        LOGGER.warning(
            "Dataset prepare request failed with domain error: dataset=%s error_type=%s message=%s",
            entry.dataset_name,
            error.error_type,
            error.message,
        )
        if error.error_type == "dataset_artifact_write_failed":
            return _server_error_response(
                error_type=error.error_type,
                message=error.message,
            )
        return _unprocessable_content_response(
            error_type=error.error_type,
            message=error.message,
        )
    except Exception:
        LOGGER.exception(
            "Dataset prepare request failed with unhandled error: dataset=%s",
            entry.dataset_name,
        )
        return _internal_server_error_response(
            message="Wystąpił nieobsłużony błąd przygotowania datasetu."
        )

    LOGGER.info(
        "Dataset prepare request succeeded: dataset=%s train=%s val=%s test=%s",
        entry.dataset_name,
        result.sample_counts.train,
        result.sample_counts.val,
        result.sample_counts.test,
    )
    return PreparedDatasetArtifactApiResponse.from_dto(result)


@datasets_controller.post(
    "/preparations",
    response_model=CreateDatasetPreparationApiResponse,
    responses={
        422: {"model": ErrorApiResponse},
        500: {"model": ErrorApiResponse},
    },
)
async def create_dataset_preparation(
    entry: CreateDatasetPreparationApiEntry,
    command_handler: CreateDatasetPreparationCommandHandler = Depends(
        get_create_dataset_preparation_command_handler
    ),
) -> CreateDatasetPreparationApiResponse | JSONResponse:
    LOGGER.info(
        "Received dataset preparation request: preparation=%s source_count=%s",
        entry.preparation_name,
        len(entry.sources),
    )
    command = CreateDatasetPreparationCommand(
        preparation_name=entry.preparation_name,
        sources=tuple(
            CreateDatasetPreparationSourceDto(
                name=source.name,
                type=source.type,
            )
            for source in entry.sources
        ),
    )

    try:
        result = command_handler.handle(command)
    except CreateDatasetPreparationCommandError as error:
        LOGGER.warning(
            "Dataset preparation request failed with domain error: preparation=%s error_type=%s message=%s",
            entry.preparation_name,
            error.error_type,
            error.message,
        )
        if error.error_type in {
            "dataset_preparation_write_failed",
            "dataset_preparation_finalize_failed",
        }:
            return _server_error_response(
                error_type=error.error_type,
                message=error.message,
            )
        return _unprocessable_content_response(
            error_type=error.error_type,
            message=error.message,
        )
    except Exception:
        LOGGER.exception(
            "Dataset preparation request failed with unhandled error: preparation=%s",
            entry.preparation_name,
        )
        return _internal_server_error_response(
            message=(
                "Wystąpił nieobsłużony błąd tworzenia przygotowania datasetu."
            )
        )

    LOGGER.info(
        "Dataset preparation request succeeded: preparation=%s status=%s source_reports=%s",
        entry.preparation_name,
        result.status,
        len(result.source_reports),
    )
    return CreateDatasetPreparationApiResponse.from_dto(result)
