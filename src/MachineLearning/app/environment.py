import os
from pathlib import Path

from dotenv import dotenv_values

APP_DIR = Path(__file__).resolve().parent
DEFAULT_ENVIRONMENT = "local"


def load_runtime_environment() -> str:
    base_values = {
        key: value
        for key, value in dotenv_values(APP_DIR / ".env").items()
        if value is not None
    }

    environment_name = (
        os.getenv("ML_ENVIRONMENT")
        or base_values.get("ML_ENVIRONMENT")
        or DEFAULT_ENVIRONMENT
    )
    overlay_values = {
        key: value
        for key, value in dotenv_values(APP_DIR / f".env.{environment_name}").items()
        if value is not None
    }

    merged_values = {**base_values, **overlay_values}

    for key, value in merged_values.items():
        os.environ.setdefault(key, value)

    return os.getenv("ML_ENVIRONMENT", environment_name)


def get_env_value(name: str, default: str) -> str:
    return os.getenv(name, default)
