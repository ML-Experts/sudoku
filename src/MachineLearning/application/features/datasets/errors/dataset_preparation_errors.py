class PrepareDatasetArtifactCommandError(Exception):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class DatasetPreparationNotFoundError(PrepareDatasetArtifactCommandError):
    def __init__(self, preparation_name: str) -> None:
        super().__init__(
            error_type="dataset_preparation_not_found",
            message=(
                f"Przygotowanie datasetu {preparation_name} nie istnieje."
            ),
        )


class DatasetPreparationSourceNotFoundError(
    PrepareDatasetArtifactCommandError
):
    def __init__(
        self,
        preparation_name: str,
        source_name: str,
        source_type: str,
    ) -> None:
        super().__init__(
            error_type="dataset_preparation_source_not_found",
            message=(
                f"Źródło {source_name} typu {source_type} nie istnieje "
                f"w przygotowaniu {preparation_name}."
            ),
        )


class DatasetPreparationLayoutInvalidError(
    PrepareDatasetArtifactCommandError
):
    def __init__(self, message: str) -> None:
        super().__init__(
            error_type="dataset_preparation_layout_invalid",
            message=message,
        )


class DatasetSourceInvalidError(PrepareDatasetArtifactCommandError):
    def __init__(self, message: str) -> None:
        super().__init__(
            error_type="dataset_source_invalid",
            message=message,
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
