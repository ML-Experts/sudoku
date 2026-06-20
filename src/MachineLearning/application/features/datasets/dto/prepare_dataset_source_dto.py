from dataclasses import dataclass


@dataclass(frozen=True)
class PrepareDatasetSourceDto:
    name: str
    type: str
    splits: tuple[str, ...]
