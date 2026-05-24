from dataclasses import dataclass


@dataclass(frozen=True)
class CellDigitInferenceResult:
    digit: int | None

    def __post_init__(self) -> None:
        if self.digit is None:
            return

        if self.digit < 1 or self.digit > 9:
            raise ValueError("Cell inference result must be null or a digit 1..9.")
