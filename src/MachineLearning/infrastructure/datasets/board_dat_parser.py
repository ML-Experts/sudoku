from pathlib import Path

from models.board_grid_label import BoardGridLabel


class BoardDatParser:
    def parse(self, dat_file_path: Path) -> BoardGridLabel:
        raw_lines = dat_file_path.read_text(encoding="utf-8").splitlines()
        if len(raw_lines) < 11:
            raise ValueError("Plik .dat nie zawiera pełnego grida 9x9.")

        grid_lines = raw_lines[2:11]
        rows: list[list[int]] = []
        for line in grid_lines:
            parts = [part for part in line.strip().split(" ") if part]
            if len(parts) != 9:
                raise ValueError("Wiersz grida .dat nie ma 9 wartości.")
            rows.append([int(part) for part in parts])

        return BoardGridLabel.from_rows(rows)
