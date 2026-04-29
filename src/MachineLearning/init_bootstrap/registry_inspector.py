from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from init_bootstrap.constants import MODEL_MANIFEST_FILE_NAME
from init_bootstrap.manifest_io import read_manifest
from init_bootstrap.validation import validate_manifest_matches_directory


@dataclass(frozen=True)
class RegistryEntryInspection:
    status: str
    reasons: list[str] = field(default_factory=list)

    @property
    def is_missing(self) -> bool:
        return self.status == "missing"

    @property
    def is_complete(self) -> bool:
        return self.status == "complete"

    @property
    def is_incomplete(self) -> bool:
        return self.status == "incomplete"


def inspect_registry_entry(
    registry_directory_path: Path, manifest: dict[str, Any]
) -> RegistryEntryInspection:
    model_directory_path = registry_directory_path / manifest["name"]
    manifest_path = model_directory_path / MODEL_MANIFEST_FILE_NAME
    artifact_path = (
        model_directory_path
        / manifest["artifacts"]["primaryArtifactRelativePath"]
    )

    if not model_directory_path.exists():
        return RegistryEntryInspection(status="missing")

    reasons: list[str] = []
    if not model_directory_path.is_dir():
        reasons.append("model_path_is_not_directory")
    if not manifest_path.is_file():
        reasons.append(MODEL_MANIFEST_FILE_NAME)
    if not artifact_path.is_file():
        reasons.append(str(manifest["artifacts"]["primaryArtifactRelativePath"]))
    elif artifact_path.stat().st_size == 0:
        reasons.append("primary_artifact_empty")

    if manifest_path.is_file():
        try:
            existing_manifest = read_manifest(manifest_path)
        except Exception:
            reasons.append("model_json_invalid")
        else:
            reasons.extend(
                validate_manifest_matches_directory(
                    existing_manifest, model_directory_path
                )
            )

    if reasons:
        return RegistryEntryInspection(
            status="incomplete", reasons=sorted(set(reasons))
        )

    return RegistryEntryInspection(status="complete")

