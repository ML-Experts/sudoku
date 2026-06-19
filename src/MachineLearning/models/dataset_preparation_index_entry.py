from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetPreparationIndexEntry:
    file_name: str
    label: int
