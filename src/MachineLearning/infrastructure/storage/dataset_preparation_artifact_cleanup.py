from pathlib import Path

from infrastructure.storage.dataset_preview_path_provider import (
    DatasetPreviewPathProvider,
)
from infrastructure.storage.dataset_preparation_workspace_manager import (
    DatasetPreparationWorkspaceManager,
)


class DatasetPreparationArtifactCleanup:
    def __init__(
        self,
        dataset_preview_path_provider: DatasetPreviewPathProvider,
    ) -> None:
        self._dataset_preview_path_provider = dataset_preview_path_provider

    def cleanup(
        self,
        dataset_name: str,
        preview_stage_dir: Path | None,
        dataset_artifact_path: Path | None,
    ) -> None:
        if preview_stage_dir is not None:
            self._dataset_preview_path_provider.delete_stage_dir(preview_stage_dir)
        self._dataset_preview_path_provider.delete_dataset_dir(dataset_name)

        if dataset_artifact_path is not None and dataset_artifact_path.exists():
            dataset_artifact_path.unlink()


class DatasetPreparationWorkspaceCleanup:
    def __init__(
        self,
        workspace_manager: DatasetPreparationWorkspaceManager,
    ) -> None:
        self._workspace_manager = workspace_manager

    def cleanup(self, preparation_name: str, stage_dir: Path | None) -> None:
        if stage_dir is not None:
            self._workspace_manager.delete_stage_dir(stage_dir)
        self._workspace_manager.delete_preparation_dir(preparation_name)
