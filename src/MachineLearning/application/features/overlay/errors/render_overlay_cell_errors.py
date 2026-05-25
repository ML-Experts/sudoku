class RenderOverlayCellCommandError(Exception):
    def __init__(self, error_type: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.status_code = status_code


class RenderOverlayCellValidationError(RenderOverlayCellCommandError):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(error_type=error_type, message=message, status_code=422)
