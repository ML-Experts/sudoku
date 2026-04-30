from dataclasses import dataclass


@dataclass(frozen=True)
class TestDigitInferenceCommand:
    image_name: str
