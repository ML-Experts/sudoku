import json
from pathlib import Path
from typing import Any

from init_bootstrap.constants import (
    ACTIVE_MODEL_FILE_NAME,
    STATUS_CREATED,
    STATUS_SKIPPED,
)
from init_bootstrap.manifest_io import read_manifest
from init_bootstrap.result import ActiveModelResult


def ensure_active_model_if_missing(
    active_model_directory_path: Path,
    registry_directory_path: Path,
    default_active_model: str | None,
    *,
    set_active_if_missing: bool,
) -> ActiveModelResult:
    if not set_active_if_missing:
        return ActiveModelResult(
            status=STATUS_SKIPPED, reason="set_active_if_missing_disabled"
        )

    active_model_directory_path.mkdir(parents=True, exist_ok=True)
    active_file_path = active_model_directory_path / ACTIVE_MODEL_FILE_NAME
    if active_file_path.exists():
        return ActiveModelResult(
            status=STATUS_SKIPPED, reason="active_model_already_set"
        )

    if not default_active_model:
        return ActiveModelResult(
            status=STATUS_SKIPPED, reason="default_active_model_missing"
        )

    manifest_path = (
        registry_directory_path
        / default_active_model
        / "model.json"
    )
    if not manifest_path.is_file():
        return ActiveModelResult(
            status=STATUS_SKIPPED,
            reason="default_active_model_not_found",
            model_name=default_active_model,
        )

    manifest = read_manifest(manifest_path)
    if not _can_use_for_inference(manifest):
        return ActiveModelResult(
            status=STATUS_SKIPPED,
            reason="model_not_inference_capable",
            model_name=default_active_model,
        )

    payload = {
        "modelName": default_active_model,
        "registryRelativePath": f"../registry/{default_active_model}",
        "setBy": "init_bootstrap",
    }
    _write_json_atomic(active_file_path, payload)
    return ActiveModelResult(
        status=STATUS_CREATED,
        model_name=default_active_model,
    )


def _can_use_for_inference(manifest: dict[str, Any]) -> bool:
    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, dict):
        return False
    if capabilities.get("canUseForInference") is not True:
        return False

    architecture = manifest.get("architecture")
    if not isinstance(architecture, dict):
        return False

    return architecture.get("numClasses") == 9


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)

