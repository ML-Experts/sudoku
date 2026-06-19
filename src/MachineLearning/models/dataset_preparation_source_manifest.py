from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetPreparationSourceManifest:
    source_names: tuple[str, ...]
