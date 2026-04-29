class TrainingEventSequence:
    def __init__(self) -> None:
        self._current = 0

    def next(self) -> int:
        self._current += 1
        return self._current
