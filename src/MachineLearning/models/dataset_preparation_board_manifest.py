from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetPreparationBoardManifest:
    board_folder_names: tuple[str, ...]
