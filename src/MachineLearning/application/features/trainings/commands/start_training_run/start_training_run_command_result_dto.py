from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StartTrainingRunCommandResultDto:
    run_name: str
    status: str
    accepted_at_utc: datetime
    warnings: tuple[str, ...] = ()
