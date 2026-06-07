from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from raw_line_family_only_pipeline_artifacts import ActiveImageSelection

if TYPE_CHECKING:
    from raw_line_family_only_bootstrap import RawLineFamilyOnlyApi


def configure_manual_image_path(
    config,
    image_path_input: str,
    repo_root: Path,
) -> str:
    if image_path_input.strip():
        typed_image_path = Path(image_path_input).expanduser()
        if not typed_image_path.is_absolute():
            typed_image_path = (repo_root / typed_image_path).resolve()

        config.image_path = typed_image_path
        return f"Manual image path enabled: {config.image_path}"

    config.image_path = None
    return (
        "Manual image path is empty. Notebook will use dataset_root + "
        "selected_dataset_index."
    )


def resolve_active_image_selection(
    config,
    notebook_api: "RawLineFamilyOnlyApi",
) -> ActiveImageSelection:
    active_image_path, dataset_images = notebook_api.resolve_active_image_path(config)
    preview_lines = [
        f"Found {len(dataset_images)} image(s) under dataset root."
    ]

    preview_paths = dataset_images[: config.preview_limit]
    for index, path in enumerate(preview_paths):
        marker = "<-- selected" if path == active_image_path else ""
        display_path = notebook_api.path_for_display(path, config.dataset_root)
        preview_lines.append(f"[{index:02d}] {display_path} {marker}".rstrip())

    if len(dataset_images) > config.preview_limit:
        preview_lines.append(
            f"... and {len(dataset_images) - config.preview_limit} more"
        )

    preview_lines.extend(("", f"Active image: {active_image_path}"))
    return ActiveImageSelection(
        active_image_path=active_image_path,
        preview_lines=tuple(preview_lines),
    )


__all__ = [
    "configure_manual_image_path",
    "resolve_active_image_selection",
]
