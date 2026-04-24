from dataclasses import dataclass


@dataclass(frozen=True)
class PreprocessingProfile:
    name: str
    output_image_size: int = 28
