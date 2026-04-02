from dataclasses import dataclass


@dataclass(frozen=True)
class BoardQuad:
    top_left: tuple[float, float]
    top_right: tuple[float, float]
    bottom_right: tuple[float, float]
    bottom_left: tuple[float, float]

    def as_clockwise_points(self) -> tuple[tuple[float, float], ...]:
        return (
            self.top_left,
            self.top_right,
            self.bottom_right,
            self.bottom_left,
        )
