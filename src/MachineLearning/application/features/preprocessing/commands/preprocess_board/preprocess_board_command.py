from dataclasses import dataclass


@dataclass(frozen=True)
class PreprocessBoardCommand:
    mime_type: str
    base64_image: str
