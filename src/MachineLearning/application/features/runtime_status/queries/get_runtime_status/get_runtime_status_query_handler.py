from datetime import datetime
from typing import Protocol

from MachineLearning.application.features.runtime_status.queries.get_runtime_status.get_runtime_status_query import (
    GetRuntimeStatusQuery,
)
from MachineLearning.application.features.runtime_status.queries.get_runtime_status.get_runtime_status_query_result_dto import (
    GetRuntimeStatusQueryResultDto,
)
from MachineLearning.models.runtime_status import RuntimeStatus

DEPENDENCY_NAME = "python-slugify"


class PackageVersionProvider(Protocol):
    def get_version(self, package_name: str) -> str: ...


class SlugifyService(Protocol):
    def slugify(self, value: str) -> str: ...


class UtcClock(Protocol):
    def now_utc(self) -> datetime: ...


class GetRuntimeStatusQueryHandler:
    def __init__(
        self,
        package_version_provider: PackageVersionProvider,
        slugify_service: SlugifyService,
        utc_clock: UtcClock,
    ) -> None:
        self._package_version_provider = package_version_provider
        self._slugify_service = slugify_service
        self._utc_clock = utc_clock

    def handle(
        self, query: GetRuntimeStatusQuery
    ) -> GetRuntimeStatusQueryResultDto:
        runtime_status = RuntimeStatus(
            status="ok",
            message=query.ping_response_message,
            service=query.service_name,
            service_slug=self._slugify_service.slugify(
                f"{query.service_name} {query.environment}"
            ),
            version=query.service_version,
            environment=query.environment,
            dependency_name=DEPENDENCY_NAME,
            dependency_version=self._package_version_provider.get_version(
                DEPENDENCY_NAME
            ),
            timestamp_utc=self._utc_clock.now_utc(),
        )

        return GetRuntimeStatusQueryResultDto.from_domain(runtime_status)
