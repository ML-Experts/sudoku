from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractCellsCommand:
    mime_type: str
    base64_image: str
