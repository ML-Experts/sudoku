from dataclasses import dataclass


@dataclass(frozen=True)
class PreprocessingImage:
    mime_type: str
    image_bytes: bytes
