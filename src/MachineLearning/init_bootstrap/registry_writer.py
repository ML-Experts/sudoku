from pathlib import Path
from typing import Any, Callable

from init_bootstrap.artifact_serializer import save_state_dict
from init_bootstrap.constants import MODEL_MANIFEST_FILE_NAME
from init_bootstrap.exceptions import (
    BootstrapRegistryEntryAlreadyExistsError,
)
from init_bootstrap.filesystem import (
    ensure_directory,
    move_directory,
    remove_directory,
    replace_directory,
)
from init_bootstrap.manifest_io import write_manifest

ArtifactSerializer = Callable[[Any, Path], None]


def write_registry_entry(
    registry_directory_path: Path,
    manifest: dict[str, Any],
    model: Any,
    *,
    overwrite: bool,
    artifact_serializer: ArtifactSerializer = save_state_dict,
) -> None:
    ensure_directory(registry_directory_path)
    model_name = manifest["name"]
    target_directory_path = registry_directory_path / model_name
    temp_directory_path = registry_directory_path / f".{model_name}.tmp"

    remove_directory(temp_directory_path)
    try:
        ensure_directory(temp_directory_path)
        artifact_path = (
            temp_directory_path
            / manifest["artifacts"]["primaryArtifactRelativePath"]
        )
        artifact_serializer(model, artifact_path)
        write_manifest(temp_directory_path / MODEL_MANIFEST_FILE_NAME, manifest)

        if not artifact_path.is_file() or artifact_path.stat().st_size == 0:
            raise RuntimeError("Temporary model artifact was not written.")
        if not (temp_directory_path / MODEL_MANIFEST_FILE_NAME).is_file():
            raise RuntimeError("Temporary model manifest was not written.")

        if target_directory_path.exists() and overwrite:
            replace_directory(temp_directory_path, target_directory_path)
        elif not target_directory_path.exists():
            move_directory(temp_directory_path, target_directory_path)
        else:
            raise BootstrapRegistryEntryAlreadyExistsError(model_name)
    except Exception:
        remove_directory(temp_directory_path)
        raise

