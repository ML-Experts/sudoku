from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BoardDatasetPair:
    group_key: str
    board_name: str
    image_path: Path
    label_path: Path


class BoardDatasetScanner:
    def scan_pairs(self, source_directory: Path) -> tuple[BoardDatasetPair, ...]:
        jpg_candidates = sorted(source_directory.rglob("*.jpg"))
        discovered_pairs: list[BoardDatasetPair] = []

        for jpg_path in jpg_candidates:
            dat_path = jpg_path.with_suffix(".dat")
            if not dat_path.is_file():
                continue

            group_key = str(jpg_path.relative_to(source_directory))
            discovered_pairs.append(
                BoardDatasetPair(
                    group_key=group_key,
                    board_name=jpg_path.stem,
                    image_path=jpg_path,
                    label_path=dat_path,
                )
            )

        if not discovered_pairs:
            raise ValueError(
                "Katalog board nie zawiera kompletnych par .jpg + .dat."
            )

        return tuple(discovered_pairs)
