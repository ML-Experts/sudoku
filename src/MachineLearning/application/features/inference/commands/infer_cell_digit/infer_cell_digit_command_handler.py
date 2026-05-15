from pathlib import Path
from typing import Protocol

import numpy as np
import torch
from numpy.typing import NDArray

from application.features.inference.commands.infer_cell_digit.infer_cell_digit_command import (
    InferCellDigitCommand,
)
from application.features.inference.commands.infer_cell_digit.infer_cell_digit_command_result_dto import (
    InferCellDigitCommandResultDto,
)
from application.features.inference.dto.cell_digit_inference_result_dto import (
    CellDigitInferenceResultDto,
)
from application.features.inference.errors.cell_digit_inference_errors import (
    CellDigitInferenceCommandError,
    CellDigitInferenceValidationError,
)
from models.cell_digit_inference_result import CellDigitInferenceResult
from models.inference_runtime_configuration import InferenceRuntimeConfiguration
from models.preprocessing_image import PreprocessingImage

INVALID_IMAGE_PAYLOAD_MESSAGE = (
    "Niepoprawny obraz wejściowy. Sprawdź poprawność MIME oraz zawartości base64."
)
CELL_IMAGE_NOT_PROCESSABLE_MESSAGE = (
    "Nie udało się przygotować obrazu komórki do inferencji."
)


class ImageCodec(Protocol):
    def decode_base64_image(
        self,
        base64_image: str,
        mime_type: str,
    ) -> PreprocessingImage: ...

    def decode_image(self, image: PreprocessingImage) -> NDArray[np.uint8]: ...


class CellPreprocessingPipeline(Protocol):
    def build_foreground_mask(
        self,
        cell_image: NDArray[np.uint8],
    ) -> NDArray[np.uint8]: ...

    def run(self, cell_image: NDArray[np.uint8]) -> NDArray[np.float32]: ...


class CellOccupancyDetector(Protocol):
    def detect(
        self,
        image: NDArray[np.float32],
        inner_margin_ratio: float,
        dark_pixel_ratio_threshold: float,
    ) -> object: ...


class RuntimeModelLoader(Protocol):
    def load(
        self,
        manifest_path: str,
        artifact_path: str,
        input_profile: str,
        inference_profile_name: str,
    ) -> object: ...


class InferCellDigitCommandHandler:
    def __init__(
        self,
        image_codec: ImageCodec,
        cell_preprocessing_pipeline: CellPreprocessingPipeline,
        cell_occupancy_detector: CellOccupancyDetector,
        runtime_model_loader: RuntimeModelLoader,
        allowed_input_mime_types: tuple[str, ...],
        supported_input_profiles: tuple[str, ...],
    ) -> None:
        self._image_codec = image_codec
        self._cell_preprocessing_pipeline = cell_preprocessing_pipeline
        self._cell_occupancy_detector = cell_occupancy_detector
        self._runtime_model_loader = runtime_model_loader
        self._allowed_input_mime_types = {
            mime_type.strip().lower() for mime_type in allowed_input_mime_types
        }
        self._supported_input_profiles = tuple(
            profile.strip() for profile in supported_input_profiles if profile.strip()
        )

    def handle(
        self,
        command: InferCellDigitCommand,
    ) -> InferCellDigitCommandResultDto:
        runtime_configuration = self._build_runtime_configuration(command)
        self._validate_command(command, runtime_configuration)

        decoded_image = self._decode_image(command)
        foreground_mask = self._build_foreground_mask(decoded_image)
        occupancy = self._detect_occupancy(foreground_mask, runtime_configuration)
        if getattr(occupancy, "is_empty", False):
            return self._to_command_result(CellDigitInferenceResult(digit=None))
        preprocessed_image = self._preprocess_cell_image(decoded_image)

        runtime_model = self._runtime_model_loader.load(
            manifest_path=command.active_model.manifest_path,
            artifact_path=command.active_model.primary_artifact_path,
            input_profile=command.active_model.input_profile,
            inference_profile_name=(
                runtime_configuration.inference_profile_name
            ),
        )

        try:
            input_tensor = runtime_model.input_transform(preprocessed_image)
            input_tensor = input_tensor.unsqueeze(0).to(runtime_model.device)
            runtime_model.model.to(runtime_model.device)
            runtime_model.model.eval()
            with torch.inference_mode():
                output = runtime_model.model(input_tensor)
                predicted_digit = int(torch.argmax(output, dim=1).item())
            inference_result = CellDigitInferenceResult(digit=predicted_digit)
        except CellDigitInferenceCommandError:
            raise
        except ValueError as error:
            raise CellDigitInferenceValidationError(
                "invalid_inference_result",
                "Model zwrócił wynik spoza zakresu produktu.",
            ) from error
        except Exception as error:
            raise CellDigitInferenceValidationError(
                "inference_runtime_failed",
                "Wystąpił błąd podczas inferencji modelu.",
            ) from error

        return self._to_command_result(inference_result)

    def _build_runtime_configuration(
        self,
        command: InferCellDigitCommand,
    ) -> InferenceRuntimeConfiguration:
        try:
            return InferenceRuntimeConfiguration(
                inference_profile_name=(
                    command.resolved_configuration.inference_profile_name
                ),
                empty_cell_inner_margin_ratio=(
                    command.resolved_configuration.empty_cell_inner_margin_ratio
                ),
                empty_cell_dark_pixel_ratio_threshold=(
                    command.resolved_configuration.empty_cell_dark_pixel_ratio_threshold
                ),
            )
        except ValueError as error:
            raise CellDigitInferenceValidationError(
                "invalid_request",
                str(error),
            ) from error

    def _validate_command(
        self,
        command: InferCellDigitCommand,
        runtime_configuration: InferenceRuntimeConfiguration,
    ) -> None:
        normalized_mime_type = command.mime_type.strip().lower()
        if (
            not normalized_mime_type
            or normalized_mime_type not in self._allowed_input_mime_types
        ):
            raise CellDigitInferenceValidationError(
                "invalid_image_payload",
                INVALID_IMAGE_PAYLOAD_MESSAGE,
            )
        if not command.base64_image.strip():
            raise CellDigitInferenceValidationError(
                "invalid_image_payload",
                INVALID_IMAGE_PAYLOAD_MESSAGE,
            )

        if not command.active_model.name.strip():
            raise CellDigitInferenceValidationError(
                "invalid_request",
                "Pole activeModel.name jest wymagane.",
            )
        if not command.active_model.input_profile.strip():
            raise CellDigitInferenceValidationError(
                "invalid_request",
                "Pole activeModel.inputProfile jest wymagane.",
            )
        self._ensure_absolute_path(
            command.active_model.manifest_path,
            "Pole activeModel.manifestPath musi być ścieżką absolutną.",
        )
        self._ensure_absolute_path(
            command.active_model.primary_artifact_path,
            "Pole activeModel.primaryArtifactPath musi być ścieżką absolutną.",
        )

        if not self._supported_input_profiles:
            raise CellDigitInferenceValidationError(
                "unsupported_input_profile",
                "Nie skonfigurowano obsługiwanych profili inferencji.",
            )
        if (
            runtime_configuration.inference_profile_name
            not in self._supported_input_profiles
        ):
            raise CellDigitInferenceValidationError(
                "unsupported_input_profile",
                "Profil inferencji nie jest obsługiwany.",
            )
        if (
            command.active_model.input_profile
            != runtime_configuration.inference_profile_name
        ):
            raise CellDigitInferenceValidationError(
                "input_profile_mismatch",
                "Profil wejściowy modelu nie pasuje do profilu inferencji.",
            )

    def _ensure_absolute_path(self, value: str, message: str) -> None:
        stripped_value = value.strip()
        if not stripped_value or not Path(stripped_value).is_absolute():
            raise CellDigitInferenceValidationError("invalid_request", message)

    def _decode_image(self, command: InferCellDigitCommand) -> NDArray[np.uint8]:
        try:
            encoded_input_image = self._image_codec.decode_base64_image(
                base64_image=command.base64_image,
                mime_type=command.mime_type,
            )
            return self._image_codec.decode_image(encoded_input_image)
        except ValueError as error:
            raise CellDigitInferenceValidationError(
                "invalid_image_payload",
                INVALID_IMAGE_PAYLOAD_MESSAGE,
            ) from error

    def _build_foreground_mask(
        self,
        decoded_image: NDArray[np.uint8],
    ) -> NDArray[np.float32]:
        try:
            foreground_mask = self._cell_preprocessing_pipeline.build_foreground_mask(
                decoded_image
            )
            return foreground_mask.astype(np.float32) / 255.0
        except ValueError as error:
            raise CellDigitInferenceValidationError(
                "cell_image_not_processable",
                CELL_IMAGE_NOT_PROCESSABLE_MESSAGE,
            ) from error

    def _preprocess_cell_image(
        self,
        decoded_image: NDArray[np.uint8],
    ) -> NDArray[np.float32]:
        try:
            return self._cell_preprocessing_pipeline.run(decoded_image)
        except ValueError as error:
            raise CellDigitInferenceValidationError(
                "cell_image_not_processable",
                CELL_IMAGE_NOT_PROCESSABLE_MESSAGE,
            ) from error

    def _detect_occupancy(
        self,
        occupancy_image: NDArray[np.float32],
        runtime_configuration: InferenceRuntimeConfiguration,
    ) -> object:
        try:
            return self._cell_occupancy_detector.detect(
                image=occupancy_image,
                inner_margin_ratio=(
                    runtime_configuration.empty_cell_inner_margin_ratio
                ),
                dark_pixel_ratio_threshold=(
                    runtime_configuration.empty_cell_dark_pixel_ratio_threshold
                ),
            )
        except ValueError as error:
            raise CellDigitInferenceValidationError(
                "cell_image_not_processable",
                CELL_IMAGE_NOT_PROCESSABLE_MESSAGE,
            ) from error

    def _to_command_result(
        self,
        result: CellDigitInferenceResult,
    ) -> InferCellDigitCommandResultDto:
        result_dto = CellDigitInferenceResultDto(digit=result.digit)
        return InferCellDigitCommandResultDto(digit=result_dto.digit)
