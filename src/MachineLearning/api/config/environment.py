import os
from pathlib import Path

from dotenv import dotenv_values

from MachineLearning.api.config.runtime_settings import RuntimeSettings

API_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ENVIRONMENT = "local"


def load_runtime_environment() -> RuntimeSettings:
    base_values = {
        key: value
        for key, value in dotenv_values(API_DIR / ".env").items()
        if value is not None
    }

    environment_name = (
        os.getenv("ML_ENVIRONMENT")
        or base_values.get("ML_ENVIRONMENT")
        or DEFAULT_ENVIRONMENT
    )
    overlay_values = {
        key: value
        for key, value in dotenv_values(API_DIR / f".env.{environment_name}").items()
        if value is not None
    }

    merged_values = {**base_values, **overlay_values}

    for key, value in merged_values.items():
        os.environ.setdefault(key, value)

    return get_runtime_settings()


def get_env_value(name: str, default: str) -> str:
    return os.getenv(name, default)


def get_runtime_settings() -> RuntimeSettings:
    return RuntimeSettings(
        environment=get_env_value("ML_ENVIRONMENT", DEFAULT_ENVIRONMENT),
        service_name=get_env_value("ML_SERVICE_NAME", "sudoku-ml"),
        service_version=get_env_value("ML_SERVICE_VERSION", "0.1.0"),
        ping_response_message=get_env_value("ML_PING_RESPONSE_MESSAGE", "pong"),
    )
