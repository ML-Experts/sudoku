from pathlib import Path

from application.features.trainings.errors.training_run_errors import (
    TrainingRunNotFoundError,
    TrainingRunValidationError,
)


class FilesystemPathValidator:
    def __init__(self, allowed_output_roots: tuple[str, ...]) -> None:
        self._allowed_output_roots = tuple(
            Path(root).expanduser().resolve()
            for root in allowed_output_roots
            if root.strip()
        )

    def ensure_file_exists(self, path: str, error_type: str) -> None:
        resolved_path = Path(path).expanduser()
        if not resolved_path.is_file():
            raise TrainingRunNotFoundError(
                error_type,
                f"Plik {resolved_path.name} nie istnieje.",
            )

    def ensure_output_paths_are_allowed(self, paths: tuple[str, ...]) -> None:
        if not self._allowed_output_roots:
            return

        for raw_path in paths:
            resolved_path = Path(raw_path).expanduser().resolve()
            if not any(
                self._is_relative_to(resolved_path, root)
                for root in self._allowed_output_roots
            ):
                raise TrainingRunValidationError(
                    "output_path_not_allowed",
                    "Ścieżka wyjściowa nie mieści się w dozwolonych katalogach.",
                )

    def _is_relative_to(self, path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
        except ValueError:
            return False
        return True
