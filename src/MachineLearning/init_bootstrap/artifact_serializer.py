from pathlib import Path
from typing import Any

from init_bootstrap.exceptions import (
    BootstrapDependencyMissingError,
    BootstrapRegistryError,
)


def save_state_dict(model: Any, path: Path) -> None:
    try:
        import torch
    except ImportError as error:
        raise BootstrapDependencyMissingError("torch") from error

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        torch.save(model.state_dict(), path)
    except Exception as error:
        raise BootstrapRegistryError(
            error_type="bootstrap_artifact_write_failed",
            message=f"Nie udalo sie zapisac artefaktu modelu: {path.name}.",
        ) from error

    if not path.is_file() or path.stat().st_size == 0:
        raise BootstrapRegistryError(
            error_type="bootstrap_artifact_write_failed",
            message=f"Artefakt modelu nie powstal albo jest pusty: {path.name}.",
        )

