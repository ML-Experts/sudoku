from dataclasses import dataclass


@dataclass(frozen=True)
class CellDigitInferenceResultDto:
    digit: int | None
