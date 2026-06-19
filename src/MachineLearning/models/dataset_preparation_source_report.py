from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetPreparationSourceReport:
    name: str
    source_type: str
    prepared_items_count: int
    rejected_items_count: int
    empty_cell_count: int
