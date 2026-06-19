class PrepareDatasetArtifactCommandError(Exception):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class UnsupportedPreprocessingProfileError(
    PrepareDatasetArtifactCommandError
):
    def __init__(self, profile_name: str) -> None:
        super().__init__(
            error_type="unsupported_preprocessing_profile",
            message=(
                f"Profil preprocessingu {profile_name} nie jest obsługiwany."
            ),
        )


class CreateDatasetPreparationCommandError(Exception):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class BoardNotFoundError(CreateDatasetPreparationCommandError):
    def __init__(self) -> None:
        super().__init__(
            error_type="board_not_found",
            message=(
                "Nie udało się wykryć żadnej poprawnej planszy Sudoku w źródle board."
            ),
        )


class DatasetPreparationWriteFailedError(CreateDatasetPreparationCommandError):
    def __init__(self, message: str) -> None:
        super().__init__(
            error_type="dataset_preparation_write_failed",
            message=message,
        )


class DatasetPreparationFinalizeFailedError(CreateDatasetPreparationCommandError):
    def __init__(self, message: str) -> None:
        super().__init__(
            error_type="dataset_preparation_finalize_failed",
            message=message,
        )
