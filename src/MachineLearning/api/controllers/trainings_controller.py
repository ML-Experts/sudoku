from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse

from api.dependencies import (
    get_cancel_training_run_command_handler,
    get_start_training_run_command_handler,
)
from api.models.error_api_response import ErrorApiResponse
from api.models.training_api_models import (
    CancelTrainingRunApiResponse,
    StartedTrainingRunApiResponse,
    StartTrainingRunApiEntry,
)
from application.features.trainings.commands.cancel_training_run.cancel_training_run_command import (
    CancelTrainingRunCommand,
)
from application.features.trainings.commands.cancel_training_run.cancel_training_run_command_handler import (
    CancelTrainingRunCommandHandler,
)
from application.features.trainings.commands.start_training_run.start_training_run_command import (
    StartTrainingRunCommand,
)
from application.features.trainings.commands.start_training_run.start_training_run_command_handler import (
    StartTrainingRunCommandHandler,
)
from application.features.trainings.dto.training_run_context_dto import (
    BaseModelReferenceDto,
    OutputRegistryModelDto,
    ProcessedDatasetReferenceDto,
    ResolvedTrainingConfigurationDto,
    TrainingParametersDto,
    TrainingOutputPathsDto,
)
from application.features.trainings.errors.training_run_errors import (
    TrainingRunCommandError,
)

trainings_controller = APIRouter(prefix="/ml/trainings", tags=["trainings"])


@trainings_controller.post(
    "",
    response_model=StartedTrainingRunApiResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"model": ErrorApiResponse},
        409: {"model": ErrorApiResponse},
        422: {"model": ErrorApiResponse},
        500: {"model": ErrorApiResponse},
    },
)
async def start_training(
    entry: StartTrainingRunApiEntry,
    background_tasks: BackgroundTasks,
    command_handler: StartTrainingRunCommandHandler = Depends(
        get_start_training_run_command_handler
    ),
) -> StartedTrainingRunApiResponse | JSONResponse:
    command = _to_start_training_run_command(entry)
    try:
        result = command_handler.handle(
            command,
            task_scheduler=background_tasks.add_task,
        )
    except TrainingRunCommandError as error:
        return _error_response(error.status_code, error.error_type, error.message)
    except Exception:
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_server_error",
            "Wystąpił nieobsłużony błąd startu treningu.",
        )

    return StartedTrainingRunApiResponse(
        run_name=result.run_name,
        status=result.status,
        accepted_at_utc=result.accepted_at_utc,
        warnings=list(result.warnings),
    )


@trainings_controller.post(
    "/{run_name}/cancel",
    response_model=CancelTrainingRunApiResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def cancel_training(
    run_name: str,
    command_handler: CancelTrainingRunCommandHandler = Depends(
        get_cancel_training_run_command_handler
    ),
) -> CancelTrainingRunApiResponse:
    result = command_handler.handle(CancelTrainingRunCommand(run_name=run_name))
    return CancelTrainingRunApiResponse(
        run_name=result.run_name,
        status=result.status,
        request_disposition=result.request_disposition,
        cancellation_requested_at_utc=result.cancellation_requested_at_utc,
    )


def _to_start_training_run_command(
    entry: StartTrainingRunApiEntry,
) -> StartTrainingRunCommand:
    return StartTrainingRunCommand(
        run_name=entry.run_name,
        base_model=BaseModelReferenceDto(
            name=entry.base_model.name,
            directory_path=entry.base_model.directory_path,
            manifest_path=entry.base_model.manifest_path,
            primary_artifact_path=entry.base_model.primary_artifact_path,
            input_profile=entry.base_model.input_profile,
            source_type=entry.base_model.source_type,
        ),
        processed_dataset=ProcessedDatasetReferenceDto(
            name=entry.processed_dataset.name,
            file_path=entry.processed_dataset.file_path,
            preprocessing_profile=entry.processed_dataset.preprocessing_profile,
        ),
        resolved_configuration=ResolvedTrainingConfigurationDto(
            training_mode=entry.resolved_configuration.training_mode,
            training_profile_name=(
                entry.resolved_configuration.training_profile_name
            ),
            augmentation_profile_name=(
                entry.resolved_configuration.augmentation_profile_name
            ),
            benchmark_name=entry.resolved_configuration.benchmark_name,
            seed=entry.resolved_configuration.seed,
            training_parameters=TrainingParametersDto(
                epochs=entry.resolved_configuration.training_parameters.epochs,
                learning_rate=(
                    entry.resolved_configuration.training_parameters.learning_rate
                ),
                batch_size=(
                    entry.resolved_configuration.training_parameters.batch_size
                ),
                early_stopping_patience=(
                    entry.resolved_configuration.training_parameters.early_stopping_patience
                ),
                early_stopping_min_delta=(
                    entry.resolved_configuration.training_parameters.early_stopping_min_delta
                ),
                warmup_epochs=(
                    entry.resolved_configuration.training_parameters.warmup_epochs
                ),
                lr_scheduler_patience=(
                    entry.resolved_configuration.training_parameters.lr_scheduler_patience
                ),
                lr_scheduler_factor=(
                    entry.resolved_configuration.training_parameters.lr_scheduler_factor
                ),
                fine_tuning_policy=(
                    entry.resolved_configuration.training_parameters.fine_tuning_policy
                ),
                use_best_checkpoint=(
                    entry.resolved_configuration.training_parameters.use_best_checkpoint
                ),
            ),
        ),
        output_model=OutputRegistryModelDto(
            name=entry.output_model.name,
            directory_path=entry.output_model.directory_path,
        ),
        output_paths=TrainingOutputPathsDto(
            run_directory_path=entry.output_paths.run_directory_path,
            report_directory_path=entry.output_paths.report_directory_path,
            benchmark_directory_path=entry.output_paths.benchmark_directory_path,
            temporary_working_directory_path=(
                entry.output_paths.temporary_working_directory_path
            ),
        ),
    )


def _error_response(
    status_code: int, error_type: str, message: str
) -> JSONResponse:
    error_response = ErrorApiResponse(error_type=error_type, message=message)
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(by_alias=True),
    )
