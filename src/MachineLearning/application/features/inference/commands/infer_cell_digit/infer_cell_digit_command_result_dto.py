from dataclasses import dataclass


@dataclass(frozen=True)
class InferCellDigitCommandResultDto:
    digit: int | None
