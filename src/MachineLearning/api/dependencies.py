from functools import lru_cache

from fastapi import Request

from api.config.runtime_settings import RuntimeSettings
from application.features.runtime_status.queries.get_runtime_status.get_runtime_status_query_handler import (
    GetRuntimeStatusQueryHandler,
)
from infrastructure.providers.package_version_provider import (
    ImportlibPackageVersionProvider,
)
from infrastructure.text.slugify_service import PythonSlugifyService
from infrastructure.time.system_utc_clock import SystemUtcClock


def get_runtime_settings(request: Request) -> RuntimeSettings:
    return request.app.state.runtime_settings


@lru_cache
def get_runtime_status_query_handler() -> GetRuntimeStatusQueryHandler:
    return GetRuntimeStatusQueryHandler(
        package_version_provider=ImportlibPackageVersionProvider(),
        slugify_service=PythonSlugifyService(),
        utc_clock=SystemUtcClock(),
    )
