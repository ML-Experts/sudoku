from dataclasses import dataclass


@dataclass(frozen=True)
class SplitSampleCountsDto:
    train: int
    val: int
    test: int
