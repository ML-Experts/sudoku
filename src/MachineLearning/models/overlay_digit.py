from dataclasses import dataclass


@dataclass(frozen=True)
class OverlayDigit:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1 or self.value > 9:
            raise ValueError("Overlay digit must be in range 1..9.")
