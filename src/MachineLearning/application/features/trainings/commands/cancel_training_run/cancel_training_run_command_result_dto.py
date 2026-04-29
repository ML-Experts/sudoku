from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CancelTrainingRunCommandResultDto:
    run_name: str
    status: str | None
    request_disposition: str
    cancellation_requested_at_utc: datetime | None
