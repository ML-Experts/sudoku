class CancelledTrainingRun(Exception):
    pass


class CancellationToken:
    def __init__(self) -> None:
        self._cancel_requested = False

    @property
    def is_cancel_requested(self) -> bool:
        return self._cancel_requested

    def request_cancel(self) -> None:
        self._cancel_requested = True

    def throw_if_cancelled(self) -> None:
        if self._cancel_requested:
            raise CancelledTrainingRun()
