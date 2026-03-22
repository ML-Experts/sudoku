from datetime import UTC, datetime
from importlib.metadata import version as package_version

from slugify import slugify

from .environment import get_env_value
from .schemas import RuntimeStatusResponse

DEPENDENCY_NAME = "python-slugify"


def build_runtime_status() -> RuntimeStatusResponse:
    environment = get_env_value("ML_ENVIRONMENT", "local")
    service_name = get_env_value("ML_SERVICE_NAME", "sudoku-ml")
    service_version = get_env_value("ML_SERVICE_VERSION", "0.1.0")
    ping_response_message = get_env_value("ML_PING_RESPONSE_MESSAGE", "pong")

    return RuntimeStatusResponse(
        status="ok",
        message=ping_response_message,
        service=service_name,
        service_slug=slugify(f"{service_name} {environment}"),
        version=service_version,
        environment=environment,
        dependency_name=DEPENDENCY_NAME,
        dependency_version=package_version(DEPENDENCY_NAME),
        timestamp_utc=datetime.now(UTC),
    )
