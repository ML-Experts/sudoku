from dataclasses import dataclass


@dataclass(frozen=True)
class SourcePreparationReport:
    name: str
    requested_type: str
    detected_type: str
    processed_sample_count: int
    included_sample_count: int
    empty_cell_count: int
    rejected_sample_count: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class PreparationReport:
    train_count: int
    val_count: int
    test_count: int
    sources: tuple[SourcePreparationReport, ...]
    warnings: tuple[str, ...]
