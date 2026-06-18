from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn

from application.features.inference.errors.cell_digit_inference_errors import (
    CellDigitInferenceValidationError,
)
from application.features.trainings.errors.training_run_errors import (
    TrainingRunValidationError,
)
from infrastructure.training.data.input_transforms import InputTransform
from models.model_manifest import ModelManifest


@dataclass(frozen=True)
class RuntimeModel:
    manifest: ModelManifest
    model: nn.Module
    input_transform: InputTransform
    device: torch.device


class RuntimeModelLoader:
    def __init__(
        self,
        manifest_reader,
        model_factory,
        artifact_loader,
        input_transform_factory,
        device_setting: str,
    ) -> None:
        self._manifest_reader = manifest_reader
        self._model_factory = model_factory
        self._artifact_loader = artifact_loader
        self._input_transform_factory = input_transform_factory
        self._device_setting = device_setting

    def load(
        self,
        manifest_path: str,
        artifact_path: str,
        input_profile: str,
        inference_profile_name: str,
    ) -> RuntimeModel:
        self._ensure_file_exists(
            manifest_path=manifest_path,
            error_type="model_manifest_not_found",
            message="Manifest aktywnego modelu inferencyjnego nie istnieje.",
        )
        self._ensure_file_exists(
            manifest_path=artifact_path,
            error_type="model_artifact_not_found",
            message="Artefakt aktywnego modelu inferencyjnego nie istnieje.",
        )

        try:
            manifest = self._manifest_reader.read(manifest_path)
        except TrainingRunValidationError as error:
            raise CellDigitInferenceValidationError(
                "model_manifest_invalid",
                "Manifest aktywnego modelu inferencyjnego jest niepoprawny.",
            ) from error

        if manifest.architecture.input_profile != input_profile:
            raise CellDigitInferenceValidationError(
                "input_profile_mismatch",
                "Profil wejściowy modelu nie pasuje do manifestu.",
            )
        if manifest.capabilities.can_use_for_inference is not True:
            raise CellDigitInferenceValidationError(
                "inference_model_not_allowed",
                "Wskazany model nie może zostać użyty do inferencji.",
            )
        if manifest.architecture.num_classes != 9:
            raise CellDigitInferenceValidationError(
                "inference_model_not_allowed",
                "Aktywny model nie obsługuje kontraktu Sudoku. "
                "Inferencja komórki wymaga dokładnie 9 klas cyfr 1..9.",
            )

        device = self._resolve_device()

        try:
            model = self._model_factory.build(manifest)
            input_transform = self._input_transform_factory.build_for_inference(
                manifest=manifest,
                inference_profile_name=inference_profile_name,
            )
            self._artifact_loader.load(
                model=model,
                artifact_path=artifact_path,
                manifest=manifest,
                device=device,
            )
        except TrainingRunValidationError as error:
            raise self._map_training_validation_error(error) from error

        return RuntimeModel(
            manifest=manifest,
            model=model,
            input_transform=input_transform,
            device=device,
        )

    def _ensure_file_exists(
        self,
        manifest_path: str,
        error_type: str,
        message: str,
    ) -> None:
        resolved_path = Path(manifest_path).expanduser()
        if not resolved_path.is_file():
            raise CellDigitInferenceValidationError(error_type, message)

    def _resolve_device(self) -> torch.device:
        device_setting = self._device_setting.strip().lower()
        if device_setting == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if device_setting == "cpu":
            return torch.device("cpu")
        if device_setting == "cuda":
            if not torch.cuda.is_available():
                raise CellDigitInferenceValidationError(
                    "inference_device_unavailable",
                    "CUDA została wskazana, ale nie jest dostępna.",
                )
            return torch.device("cuda")

        raise CellDigitInferenceValidationError(
            "unsupported_inference_device",
            "Urządzenie inferencji nie jest obsługiwane.",
        )

    def _map_training_validation_error(
        self,
        error: TrainingRunValidationError,
    ) -> CellDigitInferenceValidationError:
        if error.error_type == "unsupported_model_architecture":
            return CellDigitInferenceValidationError(
                "model_manifest_invalid",
                "Manifest aktywnego modelu zawiera nieobsługiwaną architekturę.",
            )
        if error.error_type == "unsupported_input_profile":
            return CellDigitInferenceValidationError(
                "unsupported_input_profile",
                "Profil inferencji nie jest obsługiwany.",
            )
        if error.error_type == "input_profile_mismatch":
            return CellDigitInferenceValidationError(
                "input_profile_mismatch",
                "Profil inferencji nie pasuje do manifestu modelu.",
            )
        if error.error_type == "unsupported_model_artifact_format":
            return CellDigitInferenceValidationError(
                "model_artifact_invalid",
                "Format artefaktu modelu nie jest obsługiwany.",
            )
        if error.error_type == "base_model_artifact_invalid":
            return CellDigitInferenceValidationError(
                "model_artifact_invalid",
                "Artefakt modelu inferencyjnego jest niepoprawny.",
            )

        return CellDigitInferenceValidationError(
            "inference_runtime_failed",
            "Nie udało się przygotować modelu do inferencji.",
        )
