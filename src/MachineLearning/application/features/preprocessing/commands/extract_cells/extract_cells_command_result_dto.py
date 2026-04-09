from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedCellImageDto:
    mime_type: str
    base64: str


@dataclass(frozen=True)
class ExtractCellsCommandResultDto:
    cells: tuple[tuple[ExtractedCellImageDto, ...], ...]
