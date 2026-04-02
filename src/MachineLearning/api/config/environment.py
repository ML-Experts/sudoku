import os
from pathlib import Path

from dotenv import dotenv_values

from api.config.runtime_settings import PreprocessingSettings, RuntimeSettings

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


def get_env_int(name: str, default: int) -> int:
    return int(get_env_value(name, str(default)))


def get_env_float(name: str, default: float) -> float:
    return float(get_env_value(name, str(default)))


def parse_csv_values(raw_values: str) -> tuple[str, ...]:
    items = [value.strip() for value in raw_values.split(",")]
    return tuple(item for item in items if item)


def parse_kernel_size(raw_size: str, default: tuple[int, int]) -> tuple[int, int]:
    parts = [value.strip() for value in raw_size.split(",")]
    if len(parts) != 2:
        return default

    try:
        first, second = int(parts[0]), int(parts[1])
    except ValueError:
        return default

    return first, second


def get_preprocessing_settings() -> PreprocessingSettings:
    allowed_input_mime_types = parse_csv_values(
        get_env_value(
            "ML_PREPROCESS_ALLOWED_INPUT_MIME_TYPES",
            "image/jpeg,image/jpg,image/png",
        )
    )

    return PreprocessingSettings(
        allowed_input_mime_types=allowed_input_mime_types,
        board_output_mime_type=get_env_value(
            "ML_PREPROCESS_BOARD_OUTPUT_MIME_TYPE", "image/png"
        ),
        board_output_size=get_env_int("ML_PREPROCESS_BOARD_OUTPUT_SIZE", 600),
        grayscale_color_conversion_code=get_env_int(
            "ML_PREPROCESS_GRAYSCALE_COLOR_CONVERSION_CODE", 6
        ),
        gaussian_kernel_size=parse_kernel_size(
            get_env_value("ML_PREPROCESS_GAUSSIAN_KERNEL_SIZE", "5,5"),
            default=(5, 5),
        ),
        gaussian_sigma_x=get_env_float("ML_PREPROCESS_GAUSSIAN_SIGMA_X", 0.0),
        adaptive_threshold_block_size=get_env_int(
            "ML_PREPROCESS_ADAPTIVE_THRESHOLD_BLOCK_SIZE", 11
        ),
        adaptive_threshold_c=get_env_int(
            "ML_PREPROCESS_ADAPTIVE_THRESHOLD_C", 2
        ),
        contour_retrieval_mode=get_env_int(
            "ML_PREPROCESS_CONTOUR_RETRIEVAL_MODE", 0
        ),
        contour_approximation_mode=get_env_int(
            "ML_PREPROCESS_CONTOUR_APPROXIMATION_MODE", 2
        ),
        polygon_epsilon_factor=get_env_float(
            "ML_PREPROCESS_POLYGON_EPSILON_FACTOR", 0.02
        ),
    )


def get_runtime_settings() -> RuntimeSettings:
    return RuntimeSettings(
        environment=get_env_value("ML_ENVIRONMENT", DEFAULT_ENVIRONMENT),
        service_name=get_env_value("ML_SERVICE_NAME", "sudoku-ml"),
        service_version=get_env_value("ML_SERVICE_VERSION", "0.1.0"),
        ping_response_message=get_env_value("ML_PING_RESPONSE_MESSAGE", "pong"),
        preprocessing_settings=get_preprocessing_settings(),
    )
