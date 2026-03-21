from datetime import UTC, datetime
from importlib.metadata import version as package_version

from slugify import slugify

from .schemas import RuntimeStatusResponse
from .settings import MlSettings

DEPENDENCY_NAME = "python-slugify"


def build_runtime_status(settings: MlSettings) -> RuntimeStatusResponse:
    return RuntimeStatusResponse(
        status="ok",
        message=settings.ping_response_message,
        service=settings.service_name,
        service_slug=slugify(f"{settings.service_name} {settings.environment}"),
        version=settings.service_version,
        environment=settings.environment,
        dependency_name=DEPENDENCY_NAME,
        dependency_version=package_version(DEPENDENCY_NAME),
        timestamp_utc=datetime.now(UTC),
    )
