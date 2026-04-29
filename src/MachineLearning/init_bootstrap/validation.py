from pathlib import Path
from typing import Any

from init_bootstrap.constants import (
    ARTIFACT_FORMAT_PYTORCH_STATE_DICT,
    FRAMEWORK_PYTORCH,
    SOURCE_TYPE_BOOTSTRAP,
)
from init_bootstrap.exceptions import BootstrapConfigurationError
from init_bootstrap.naming import validate_model_name

Manifest = dict[str, Any]


def _get_nested(manifest: Manifest, keys: tuple[str, ...]) -> Any:
    current: Any = manifest
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            raise BootstrapConfigurationError(
                error_type="bootstrap_manifest_invalid",
                message=f"Manifest nie zawiera pola {'.'.join(keys)}.",
            )
        current = current[key]
    return current


def validate_manifest_contract(manifest: Manifest) -> None:
    name = _get_nested(manifest, ("name",))
    if not isinstance(name, str):
        raise BootstrapConfigurationError(
            error_type="bootstrap_manifest_invalid",
            message="Pole manifestu 'name' musi byc tekstem.",
        )
    validate_model_name(name)

    if manifest.get("sourceType") != SOURCE_TYPE_BOOTSTRAP:
        raise BootstrapConfigurationError(
            error_type="bootstrap_manifest_invalid",
            message="Manifest bootstrap musi miec sourceType='bootstrap'.",
        )
    if manifest.get("sourceRunName") is not None:
        raise BootstrapConfigurationError(
            error_type="bootstrap_manifest_invalid",
            message="Manifest bootstrap musi miec sourceRunName=null.",
        )
    if manifest.get("framework") != FRAMEWORK_PYTORCH:
        raise BootstrapConfigurationError(
            error_type="bootstrap_manifest_invalid",
            message="MVP initu obsluguje tylko framework='pytorch'.",
        )

    required_fields = (
        ("architecture", "type"),
        ("architecture", "family"),
        ("architecture", "numClasses"),
        ("architecture", "inputChannels"),
        ("architecture", "inputHeight"),
        ("architecture", "inputWidth"),
        ("architecture", "inputProfile"),
        ("artifacts", "primaryArtifactRelativePath"),
        ("artifacts", "format"),
        ("capabilities", "canStartTraining"),
        ("capabilities", "canUseForInference"),
    )
    for field_path in required_fields:
        _get_nested(manifest, field_path)

    artifact_relative_path = _get_nested(
        manifest, ("artifacts", "primaryArtifactRelativePath")
    )
    if (
        not isinstance(artifact_relative_path, str)
        or not artifact_relative_path
        or Path(artifact_relative_path).is_absolute()
    ):
        raise BootstrapConfigurationError(
            error_type="bootstrap_manifest_invalid",
            message=(
                "artifacts.primaryArtifactRelativePath musi byc niepusta "
                "sciezka wzgledna."
            ),
        )

    if manifest["artifacts"]["format"] != ARTIFACT_FORMAT_PYTORCH_STATE_DICT:
        raise BootstrapConfigurationError(
            error_type="bootstrap_manifest_invalid",
            message=(
                "MVP initu obsluguje tylko format "
                "'pytorch-state-dict'."
            ),
        )

    for capability in ("canStartTraining", "canUseForInference"):
        if not isinstance(manifest["capabilities"][capability], bool):
            raise BootstrapConfigurationError(
                error_type="bootstrap_manifest_invalid",
                message=f"capabilities.{capability} musi byc boolean.",
            )


def validate_manifest_matches_directory(
    manifest: Manifest, model_directory_path: Path
) -> list[str]:
    reasons: list[str] = []
    if manifest.get("name") != model_directory_path.name:
        reasons.append("model_name_mismatch")
    if manifest.get("sourceType") != SOURCE_TYPE_BOOTSTRAP:
        reasons.append("source_type_not_bootstrap")
    if manifest.get("sourceRunName") is not None:
        reasons.append("source_run_name_not_null")
    return reasons

