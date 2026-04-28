from dataclasses import dataclass


@dataclass(frozen=True)
class SplitRatiosDto:
    train: float
    val: float
    test: float


@dataclass(frozen=True)
class DatasetSplitPolicyDto:
    mode: str
    ratios: SplitRatiosDto
    group_by: str
