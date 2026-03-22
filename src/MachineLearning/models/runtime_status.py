from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RuntimeStatus:
    status: str
    message: str
    service: str
    service_slug: str
    version: str
    environment: str
    dependency_name: str
    dependency_version: str
    timestamp_utc: datetime
