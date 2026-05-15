from dataclasses import dataclass


@dataclass(frozen=True)
class TrainingProfile:
    name: str
    architecture_family: str
    epochs: int
    batch_size: int
    learning_rate: float
    optimizer: str
    fine_tuning_policy: str
    early_stopping_patience: int | None = None
    early_stopping_min_delta: float = 0.0
    lr_scheduler_patience: int | None = None
    lr_scheduler_factor: float | None = None
