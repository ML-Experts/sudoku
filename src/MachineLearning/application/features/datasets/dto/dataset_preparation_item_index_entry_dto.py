from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetPreparationItemIndexEntryDto:
    file_name: str
    label: int
