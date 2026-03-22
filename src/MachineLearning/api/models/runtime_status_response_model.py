from datetime import datetime

from pydantic import BaseModel, ConfigDict

from MachineLearning.application.features.runtime_status.queries.get_runtime_status.get_runtime_status_query_result_dto import (
    GetRuntimeStatusQueryResultDto,
)


class RuntimeStatusResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    def from_dto(
        cls, runtime_status_result: GetRuntimeStatusQueryResultDto
    ) -> "RuntimeStatusResponseModel":
        return cls(
            status=runtime_status_result.status,
            message=runtime_status_result.message,
            service=runtime_status_result.service,
            service_slug=runtime_status_result.service_slug,
            version=runtime_status_result.version,
            environment=runtime_status_result.environment,
            dependency_name=runtime_status_result.dependency_name,
            dependency_version=runtime_status_result.dependency_version,
            timestamp_utc=runtime_status_result.timestamp_utc,
        )
