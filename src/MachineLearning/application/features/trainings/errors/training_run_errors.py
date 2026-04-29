class TrainingRunCommandError(Exception):
    def __init__(
        self,
        error_type: str,
        message: str,
        status_code: int,
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.status_code = status_code


class TrainingRunNotFoundError(TrainingRunCommandError):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(error_type, message, 404)


class TrainingRunConflictError(TrainingRunCommandError):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(error_type, message, 409)


class TrainingRunValidationError(TrainingRunCommandError):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(error_type, message, 422)
