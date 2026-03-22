from dataclasses import dataclass
from datetime import datetime

from MachineLearning.models.runtime_status import RuntimeStatus


@dataclass(frozen=True)
class GetRuntimeStatusQueryResultDto:
    status: str
    message: str
    service: str
    service_slug: str
    version: str
    environment: str
    dependency_name: str
    dependency_version: str
    timestamp_utc: datetime

    @classmethod
    def from_domain(
        cls, runtime_status: RuntimeStatus
    ) -> "GetRuntimeStatusQueryResultDto":
        return cls(
            status=runtime_status.status,
            message=runtime_status.message,
            service=runtime_status.service,
            service_slug=runtime_status.service_slug,
            version=runtime_status.version,
            environment=runtime_status.environment,
            dependency_name=runtime_status.dependency_name,
            dependency_version=runtime_status.dependency_version,
            timestamp_utc=runtime_status.timestamp_utc,
        )
