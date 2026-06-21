from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import ExperimentConfig


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
RUNTIME_ROOT_MARKERS = (
    "api",
    "application",
    "infrastructure",
    "models",
    "requirements.txt",
)


def _looks_like_runtime_root(candidate: Path) -> bool:
    return all((candidate / marker).exists() for marker in RUNTIME_ROOT_MARKERS)


def find_runtime_root(start_path: Path | None = None) -> Path:
    current_path = (start_path or Path.cwd()).resolve()
    if current_path.is_file():
        current_path = current_path.parent

    for candidate in [current_path, *current_path.parents]:
        if _looks_like_runtime_root(candidate):
            return candidate

        nested_runtime_root = candidate / "src" / "MachineLearning"
        if _looks_like_runtime_root(nested_runtime_root):
            return nested_runtime_root

    raise FileNotFoundError(
        "Could not locate MachineLearning runtime root from the current working directory."
    )


PROJECT_ROOT = find_runtime_root(Path(__file__).resolve().parent)
# Backwards-compatible alias kept for older draft tooling.
REPO_ROOT = PROJECT_ROOT


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
    dataset_images = (
        []
        if config.dataset_root is None
        else discover_dataset_images(config.dataset_root)
    )

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
    "PROJECT_ROOT",
    "REPO_ROOT",
    "discover_dataset_images",
    "find_repo_root",
    "find_runtime_root",
    "path_for_display",
    "resolve_active_image_path",
]


def find_repo_root(start_path: Path | None = None) -> Path:
    return find_runtime_root(start_path)
