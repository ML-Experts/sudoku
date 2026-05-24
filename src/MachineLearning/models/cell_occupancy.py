from dataclasses import dataclass


@dataclass(frozen=True)
class CellOccupancy:
    is_empty: bool
    dark_pixel_ratio: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.dark_pixel_ratio <= 1.0:
            raise ValueError("Dark pixel ratio must be in range [0.0, 1.0].")
