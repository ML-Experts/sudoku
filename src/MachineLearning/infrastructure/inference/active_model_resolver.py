import json
from pathlib import Path
from typing import Any

from application.features.inference.dto.active_model_reference_dto import (
    ActiveModelReferenceDto,
)
from application.features.inference.errors.test_digit_inference_errors import (
    TestDigitInferenceCommandError,
)


class FilesystemActiveModelResolver:
    def __init__(
        self,
        active_model_directory_path: str,
        registry_directory_path: str,
    ) -> None:
        self._active_model_directory_path = Path(active_model_directory_path)
        self._registry_directory_path = Path(registry_directory_path)

    def resolve(self) -> ActiveModelReferenceDto:
        active_model_path = self._active_model_directory_path / "inference.json"
        if not active_model_path.is_file():
            raise TestDigitInferenceCommandError(
                status_code=404,
                error_type="active_inference_model_not_found",
                message="Nie wskazano aktywnego modelu inferencyjnego.",
            )

        active_model_payload = self._read_json(
            active_model_path,
            error_type="active_inference_model_invalid",
            message="Wskaźnik aktywnego modelu jest niepoprawny.",
        )
        model_name = active_model_payload.get("modelName")
        if (
            not isinstance(model_name, str)
            or not model_name.strip()
            or Path(model_name).name != model_name
        ):
            raise TestDigitInferenceCommandError(
                status_code=422,
                error_type="active_inference_model_invalid",
                message="Wskaźnik aktywnego modelu zawiera niepoprawny modelName.",
            )

        model_directory_path = self._registry_directory_path / model_name
        manifest_path = model_directory_path / "model.json"
        if not manifest_path.is_file():
            raise TestDigitInferenceCommandError(
                status_code=404,
                error_type="inference_model_manifest_not_found",
                message="Manifest aktywnego modelu nie istnieje.",
            )

        manifest_payload = self._read_json(
            manifest_path,
            error_type="inference_model_manifest_invalid",
            message="Manifest aktywnego modelu jest niepoprawny.",
        )
        self._ensure_model_can_use_for_inference(manifest_payload)
        artifact_relative_path = self._get_primary_artifact_relative_path(
            manifest_payload
        )
        artifact_path = model_directory_path / artifact_relative_path
        if not artifact_path.is_file():
            raise TestDigitInferenceCommandError(
                status_code=404,
                error_type="inference_model_artifact_not_found",
                message="Artefakt aktywnego modelu nie istnieje.",
            )

        return ActiveModelReferenceDto(
            model_name=model_name,
            model_directory_path=str(model_directory_path),
            manifest_path=str(manifest_path),
            primary_artifact_path=str(artifact_path),
        )

    def _read_json(
        self,
        path: Path,
        error_type: str,
        message: str,
    ) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise TestDigitInferenceCommandError(
                status_code=422,
                error_type=error_type,
                message=message,
            ) from error

        if not isinstance(payload, dict):
            raise TestDigitInferenceCommandError(
                status_code=422,
                error_type=error_type,
                message=message,
            )
        return payload

    def _ensure_model_can_use_for_inference(
        self,
        manifest_payload: dict[str, Any],
    ) -> None:
        capabilities = manifest_payload.get("capabilities")
        if (
            not isinstance(capabilities, dict)
            or capabilities.get("canUseForInference") is not True
        ):
            raise TestDigitInferenceCommandError(
                status_code=422,
                error_type="inference_model_not_allowed",
                message="Aktywny model nie może być użyty do inferencji.",
            )

    def _get_primary_artifact_relative_path(
        self,
        manifest_payload: dict[str, Any],
    ) -> Path:
        artifacts = manifest_payload.get("artifacts")
        if not isinstance(artifacts, dict):
            raise TestDigitInferenceCommandError(
                status_code=422,
                error_type="inference_model_manifest_invalid",
                message="Manifest modelu nie zawiera sekcji artifacts.",
            )

        raw_relative_path = artifacts.get("primaryArtifactRelativePath")
        if not isinstance(raw_relative_path, str) or not raw_relative_path.strip():
            raise TestDigitInferenceCommandError(
                status_code=422,
                error_type="inference_model_manifest_invalid",
                message="Manifest modelu nie zawiera głównego artefaktu.",
            )

        relative_path = Path(raw_relative_path)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise TestDigitInferenceCommandError(
                status_code=422,
                error_type="inference_model_manifest_invalid",
                message="Ścieżka artefaktu modelu musi być względna.",
            )
        return relative_path
