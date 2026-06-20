from dataclasses import dataclass


@dataclass(frozen=True)
class CellOccupancy:
    is_empty: bool
    foreground_pixel_count: int
    foreground_pixel_ratio: float
    filtered_segment_count: int
    accept_by_pixels: bool
    accept_by_segments: bool

    def __post_init__(self) -> None:
        if self.foreground_pixel_count < 0:
            raise ValueError("Foreground pixel count cannot be negative.")
        if not 0.0 <= self.foreground_pixel_ratio <= 1.0:
            raise ValueError("Foreground pixel ratio must be in range [0.0, 1.0].")
        if self.filtered_segment_count < 0:
            raise ValueError("Filtered segment count cannot be negative.")

    @property
    def dark_pixel_ratio(self) -> float:
        return self.foreground_pixel_ratio
