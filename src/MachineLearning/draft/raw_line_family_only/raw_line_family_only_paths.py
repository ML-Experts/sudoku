from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from raw_line_family_only_models import ExperimentConfig


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def find_repo_root(start_path: Path | None = None) -> Path:
    current_path = (start_path or Path.cwd()).resolve()
    for candidate in [current_path, *current_path.parents]:
        if (candidate / ".git").exists() or (candidate / ".ai").exists():
            return candidate
    raise FileNotFoundError(
        "Could not locate repository root from the current working directory."
    )


REPO_ROOT = find_repo_root(Path(__file__).resolve().parent)


def discover_dataset_images(dataset_root: Path) -> list[Path]:
    if not dataset_root.exists():
        return []

    return sorted(
        path
        for path in dataset_root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def path_for_display(path: Path, base_path: Path) -> str:
    try:
        return str(path.relative_to(base_path))
    except ValueError:
        return str(path)


def resolve_active_image_path(
    config: "ExperimentConfig",
) -> tuple[Path, list[Path]]:
    dataset_images = discover_dataset_images(config.dataset_root)

    if config.image_path is not None:
        image_path = config.image_path.resolve()
        if not image_path.exists():
            raise FileNotFoundError(f"Configured image does not exist: {image_path}")
        return image_path, dataset_images

    if not dataset_images:
        raise FileNotFoundError(
            "No dataset images found. Set CONFIG.dataset_root or CONFIG.image_path first."
        )

    selected_index = max(
        0,
        min(config.selected_dataset_index, len(dataset_images) - 1),
    )
    return dataset_images[selected_index], dataset_images


__all__ = [
    "IMAGE_EXTENSIONS",
    "REPO_ROOT",
    "discover_dataset_images",
    "find_repo_root",
    "path_for_display",
    "resolve_active_image_path",
]
