from dataclasses import dataclass


@dataclass(frozen=True)
class TestDigitInferenceResultDto:
    digit: int
