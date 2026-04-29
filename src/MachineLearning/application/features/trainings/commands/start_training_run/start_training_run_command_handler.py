from typing import Callable

from application.features.trainings.commands.start_training_run.start_training_run_command import (
    StartTrainingRunCommand,
)
from application.features.trainings.commands.start_training_run.start_training_run_command_result_dto import (
    StartTrainingRunCommandResultDto,
)
from application.features.trainings.dto.training_run_context_dto import (
    TrainingRunContextDto,
)
from application.features.trainings.errors.training_run_errors import (
    TrainingRunValidationError,
)
from application.features.trainings.ports.training_ports import (
    ActiveTrainingRunGuard,
    FilesystemPathValidator,
    ModelManifestReader,
    TrainingRunner,
    UtcClock,
)


class StartTrainingRunCommandHandler:
    def __init__(
        self,
        manifest_reader: ModelManifestReader,
        path_validator: FilesystemPathValidator,
        active_run_guard: ActiveTrainingRunGuard,
        training_runner: TrainingRunner,
        utc_clock: UtcClock,
    ) -> None:
        self._manifest_reader = manifest_reader
        self._path_validator = path_validator
        self._active_run_guard = active_run_guard
        self._training_runner = training_runner
        self._utc_clock = utc_clock

    def handle(
        self,
        command: StartTrainingRunCommand,
        task_scheduler: Callable[..., None],
    ) -> StartTrainingRunCommandResultDto:
        self._validate_command(command)
        self._active_run_guard.ensure_no_active_run()
        self._path_validator.ensure_file_exists(
            command.base_model.manifest_path,
            "base_model_manifest_not_found",
        )
        self._path_validator.ensure_file_exists(
            command.base_model.primary_artifact_path,
            "base_model_artifact_not_found",
        )
        self._path_validator.ensure_file_exists(
            command.processed_dataset.file_path,
            "processed_dataset_not_found",
        )
        self._path_validator.ensure_output_paths_are_allowed(
            (
                command.output_model.directory_path,
                command.output_paths.run_directory_path,
                command.output_paths.report_directory_path,
                command.output_paths.temporary_working_directory_path,
            )
        )

        manifest = self._manifest_reader.read(command.base_model.manifest_path)
        self._validate_manifest(command, manifest)

        context = TrainingRunContextDto(
            run_name=command.run_name,
            base_model=command.base_model,
            processed_dataset=command.processed_dataset,
            resolved_configuration=command.resolved_configuration,
            output_model=command.output_model,
            output_paths=command.output_paths,
            model_manifest=manifest,
        )
        cancellation_token = self._active_run_guard.reserve(command.run_name)
        try:
            task_scheduler(
                self._training_runner.start,
                context,
                cancellation_token,
            )
        except Exception:
            self._active_run_guard.release(command.run_name)
            raise

        return StartTrainingRunCommandResultDto(
            run_name=command.run_name,
            status="queued",
            accepted_at_utc=self._utc_clock.now(),
            warnings=(),
        )

    def _validate_command(self, command: StartTrainingRunCommand) -> None:
        if (
            command.base_model.input_profile
            != command.processed_dataset.preprocessing_profile
        ):
            raise TrainingRunValidationError(
                "training_input_profile_mismatch",
                "Profil wejściowy modelu bazowego nie pasuje do profilu datasetu.",
            )

        if command.resolved_configuration.training_mode != "fineTuning":
            raise TrainingRunValidationError(
                "unsupported_training_mode",
                "Obsługiwany jest wyłącznie tryb fineTuning.",
            )

    def _validate_manifest(self, command: StartTrainingRunCommand, manifest) -> None:
        if manifest.framework != "pytorch":
            raise TrainingRunValidationError(
                "unsupported_model_framework",
                "Manifest modelu musi deklarować framework pytorch.",
            )

        if manifest.architecture.input_profile != command.base_model.input_profile:
            raise TrainingRunValidationError(
                "manifest_input_profile_mismatch",
                "Profil wejściowy manifestu nie pasuje do wskazanego modelu.",
            )

        if manifest.architecture.family not in {"cnn", "resnet"}:
            raise TrainingRunValidationError(
                "unsupported_model_architecture",
                "Rodzina architektury modelu nie jest obsługiwana.",
            )
