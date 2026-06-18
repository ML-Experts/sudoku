from typing import Protocol

import numpy as np
import torch
from numpy.typing import NDArray

from application.features.inference.commands.test_digit_inference.test_digit_inference_command import (
    TestDigitInferenceCommand,
)
from application.features.inference.dto.active_model_reference_dto import (
    ActiveModelReferenceDto,
)
from application.features.inference.dto.test_digit_inference_result_dto import (
    TestDigitInferenceResultDto,
)
from application.features.inference.errors.test_digit_inference_errors import (
    TestDigitInferenceCommandError,
)
from application.features.trainings.errors.training_run_errors import (
    TrainingRunValidationError,
)


class TestImageRepository(Protocol):
    def load(self, image_name: str) -> NDArray[np.uint8]: ...


class ActiveModelResolver(Protocol):
    def resolve(self) -> ActiveModelReferenceDto: ...


class TestDigitInferenceCommandHandler:
    def __init__(
        self,
        image_repository: TestImageRepository,
        active_model_resolver: ActiveModelResolver,
        manifest_reader,
        model_factory,
        artifact_loader,
        input_transform_factory,
        cell_preprocessing_pipeline,
        device_setting: str,
    ) -> None:
        self._image_repository = image_repository
        self._active_model_resolver = active_model_resolver
        self._manifest_reader = manifest_reader
        self._model_factory = model_factory
        self._artifact_loader = artifact_loader
        self._input_transform_factory = input_transform_factory
        self._cell_preprocessing_pipeline = cell_preprocessing_pipeline
        self._device_setting = device_setting

    def handle(
        self,
        command: TestDigitInferenceCommand,
    ) -> TestDigitInferenceResultDto:
        image = self._image_repository.load(command.image_name)
        model_reference = self._active_model_resolver.resolve()

        try:
            manifest = self._manifest_reader.read(model_reference.manifest_path)
            model = self._model_factory.build(manifest)
            device = self._resolve_device()
            self._artifact_loader.load(
                model=model,
                artifact_path=model_reference.primary_artifact_path,
                manifest=manifest,
                device=device,
            )
            input_transform = self._input_transform_factory.build(
                manifest=manifest,
                augmentation_profile_name="digits-light-v1",
            )
        except TrainingRunValidationError as error:
            raise TestDigitInferenceCommandError(
                status_code=422,
                error_type=error.error_type,
                message=error.message,
            ) from error

        try:
            preprocessed_image = self._cell_preprocessing_pipeline.run(image)
        except ValueError as error:
            raise TestDigitInferenceCommandError(
                status_code=422,
                error_type="test_image_preprocessing_failed",
                message="Nie udało się przygotować obrazka do inferencji.",
            ) from error

        input_tensor = input_transform(preprocessed_image).unsqueeze(0).to(device)

        model.to(device)
        model.eval()
        with torch.inference_mode():
            output = model(input_tensor)
            class_index = int(torch.argmax(output, dim=1).item())
            digit = self._map_class_index_to_digit(
                class_index,
                manifest.architecture.num_classes,
            )

        return TestDigitInferenceResultDto(digit=digit)

    def _map_class_index_to_digit(
        self,
        class_index: int,
        num_classes: int,
    ) -> int:
        if num_classes == 9:
            return class_index + 1
        if num_classes == 10:
            return class_index
        raise TestDigitInferenceCommandError(
            status_code=422,
            error_type="unsupported_model_architecture",
            message="Aktywny model ma nieobsługiwany kontrakt liczby klas.",
        )

    def _resolve_device(self) -> torch.device:
        device_setting = self._device_setting.strip().lower()
        if device_setting == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if device_setting == "cpu":
            return torch.device("cpu")
        if device_setting == "cuda":
            if not torch.cuda.is_available():
                raise TestDigitInferenceCommandError(
                    status_code=422,
                    error_type="inference_device_unavailable",
                    message="CUDA została wskazana, ale nie jest dostępna.",
                )
            return torch.device("cuda")
        raise TestDigitInferenceCommandError(
            status_code=422,
            error_type="unsupported_inference_device",
            message="Urządzenie inferencji nie jest obsługiwane.",
        )
