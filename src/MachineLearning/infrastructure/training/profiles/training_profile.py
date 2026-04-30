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
