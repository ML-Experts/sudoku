from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResolvedDatasetSource:
    name: str
    requested_type: str
    detected_type: str
    path: Path
    images_path: Path | None = None
    labels_path: Path | None = None


class DatasetSourceResolver:
    def __init__(self, boards_subdirectory: str, digits_subdirectory: str) -> None:
        self._boards_subdirectory = Path(boards_subdirectory)
        self._digits_subdirectory = Path(digits_subdirectory)

    def resolve(self, source_name: str, requested_type: str) -> ResolvedDatasetSource:
        normalized_type = requested_type.strip().lower()
        if normalized_type == "board":
            board_path = self._boards_subdirectory / source_name
            if not board_path.is_dir():
                raise ValueError(f"Nie znaleziono katalogu board {source_name}.")
            return ResolvedDatasetSource(
                name=source_name,
                requested_type=normalized_type,
                detected_type="board",
                path=board_path,
            )

        if normalized_type == "digit":
            images_path = self._digits_subdirectory / f"{source_name}.idx3-ubyte"
            labels_path = self._digits_subdirectory / f"{source_name}.idx1-ubyte"
            if not images_path.is_file() or not labels_path.is_file():
                raise ValueError(
                    f"Nie znaleziono kompletnej pary IDX dla {source_name}."
                )
            return ResolvedDatasetSource(
                name=source_name,
                requested_type=normalized_type,
                detected_type="digit",
                path=self._digits_subdirectory,
                images_path=images_path,
                labels_path=labels_path,
            )

        raise ValueError(f"Nieobsługiwany typ źródła {requested_type}.")
