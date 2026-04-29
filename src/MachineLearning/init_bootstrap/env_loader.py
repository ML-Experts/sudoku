import os
from pathlib import Path

from init_bootstrap.constants import ENVIRONMENT_VARIABLE_NAME

DEFAULT_ENVIRONMENT = "local"


def get_bootstrap_dir() -> Path:
    return Path(__file__).resolve().parent


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        values[key] = value

    return values


def load_environment(
    env_file: Path | None = None,
    bootstrap_dir: Path | None = None,
) -> dict[str, str]:
    init_dir = bootstrap_dir or get_bootstrap_dir()
    base_env_path = env_file or init_dir / ".env"
    base_values = _load_env_file(base_env_path)

    environment_name = (
        os.getenv(ENVIRONMENT_VARIABLE_NAME)
        or base_values.get(ENVIRONMENT_VARIABLE_NAME)
        or DEFAULT_ENVIRONMENT
    ).strip()

    overlay_values: dict[str, str] = {}
    if env_file is None:
        overlay_env_path = init_dir / f".env.{environment_name}"
        overlay_values = _load_env_file(overlay_env_path)

    merged_values = {**base_values, **overlay_values}
    for key, value in merged_values.items():
        os.environ.setdefault(key, value)

    return {**merged_values, **os.environ}

