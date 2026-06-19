from dataclasses import dataclass


@dataclass(frozen=True)
class CreateDatasetPreparationSourceDto:
    name: str
    type: str
