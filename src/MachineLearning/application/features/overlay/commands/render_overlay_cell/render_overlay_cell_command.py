from dataclasses import dataclass


@dataclass(frozen=True)
class RenderOverlayCellCommand:
    mime_type: str
    base64_image: str
    digit: int
    row_index: int | None = None
    column_index: int | None = None
