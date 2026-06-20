from pathlib import Path


class ProcessedDatasetArtifactCleanup:
    def cleanup(self, dataset_artifact_path: Path | None) -> None:
        if dataset_artifact_path is None:
            return
        if dataset_artifact_path.exists():
            dataset_artifact_path.unlink()
