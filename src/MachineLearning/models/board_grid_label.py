from dataclasses import dataclass


@dataclass(frozen=True)
class BoardGridLabel:
    rows: tuple[tuple[int, ...], ...]

    @classmethod
    def from_rows(cls, rows: list[list[int]]) -> "BoardGridLabel":
        if len(rows) != 9:
            raise ValueError("Board labels must contain exactly 9 rows.")

        normalized_rows: list[tuple[int, ...]] = []
        for row in rows:
            if len(row) != 9:
                raise ValueError(
                    "Board labels must contain exactly 9 columns in each row."
                )
            normalized_rows.append(tuple(row))

        return cls(rows=tuple(normalized_rows))

    def flatten(self) -> tuple[int, ...]:
        flattened: list[int] = []
        for row in self.rows:
            flattened.extend(row)
        return tuple(flattened)
