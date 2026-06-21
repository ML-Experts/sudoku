from dataclasses import dataclass


@dataclass(frozen=True)
class BoardCellPreviewEntry:
    cell_index: int
    label: int | None
    preview_image_relative_path: str
    included_in_dataset: bool


@dataclass(frozen=True)
class BoardPreviewEntry:
    board_name: str
    split: str
    corrected_board_image_relative_path: str
    cells: tuple[BoardCellPreviewEntry, ...]


@dataclass(frozen=True)
class BoardSourcePreview:
    source_name: str
    boards: tuple[BoardPreviewEntry, ...]


@dataclass(frozen=True)
class DigitSamplePreviewEntry:
    sample_index: str
    split: str
    label: int
    preview_image_relative_path: str
    included_in_dataset: bool


@dataclass(frozen=True)
class DigitSourcePreview:
    source_name: str
    samples: tuple[DigitSamplePreviewEntry, ...]


@dataclass(frozen=True)
class DatasetPreviewIndex:
    dataset_name: str
    preprocessing_profile: str
    board_sources: tuple[BoardSourcePreview, ...]
    digit_sources: tuple[DigitSourcePreview, ...]
