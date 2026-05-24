from dataclasses import dataclass


@dataclass(frozen=True)
class CancelTrainingRunCommand:
    run_name: str
