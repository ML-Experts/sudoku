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


def get_env_optional_positive_int(
    name: str, default: int | None = None
) -> int | None:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    stripped_value = raw_value.strip()
    if not stripped_value:
        return None

    parsed_value = int(stripped_value)
    if parsed_value <= 0:
        return None

    return parsed_value


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
        board_output_padding_pixels=get_env_int(
            "ML_PREPROCESS_BOARD_OUTPUT_PADDING_PIXELS", 8
        ),
        board_refinement_passes=get_env_int(
            "ML_PREPROCESS_BOARD_REFINEMENT_PASSES", 1
        ),
        cells_grid_rows=get_env_int("ML_PREPROCESS_CELLS_GRID_ROWS", 9),
        cells_grid_cols=get_env_int("ML_PREPROCESS_CELLS_GRID_COLS", 9),
        cells_inner_margin_ratio=get_env_float(
            "ML_PREPROCESS_CELLS_INNER_MARGIN_RATIO", 0.08
        ),
        cells_minimum_cell_size_px=get_env_int(
            "ML_PREPROCESS_CELLS_MINIMUM_CELL_SIZE_PX", 8
        ),
        cells_output_cell_size=get_env_optional_positive_int(
            "ML_PREPROCESS_CELLS_OUTPUT_CELL_SIZE"
        ),
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
        board_edge_canny_threshold_1=get_env_int(
            "ML_PREPROCESS_BOARD_EDGE_CANNY_THRESHOLD_1", 50
        ),
        board_edge_canny_threshold_2=get_env_int(
            "ML_PREPROCESS_BOARD_EDGE_CANNY_THRESHOLD_2", 150
        ),
        board_edge_hough_threshold=get_env_int(
            "ML_PREPROCESS_BOARD_EDGE_HOUGH_THRESHOLD", 80
        ),
        board_edge_min_line_length_ratio=get_env_float(
            "ML_PREPROCESS_BOARD_EDGE_MIN_LINE_LENGTH_RATIO", 0.2
        ),
        board_edge_max_line_gap_ratio=get_env_float(
            "ML_PREPROCESS_BOARD_EDGE_MAX_LINE_GAP_RATIO", 0.04
        ),
        board_edge_angle_tolerance_degrees=get_env_float(
            "ML_PREPROCESS_BOARD_EDGE_ANGLE_TOLERANCE_DEGREES", 12.0
        ),
        board_edge_outer_line_window_ratio=get_env_float(
            "ML_PREPROCESS_BOARD_EDGE_OUTER_LINE_WINDOW_RATIO", 0.1
        ),
        board_edge_minimum_board_area_ratio=get_env_float(
            "ML_PREPROCESS_BOARD_EDGE_MINIMUM_BOARD_AREA_RATIO", 0.1
        ),
        board_edge_minimum_family_segments=get_env_int(
            "ML_PREPROCESS_BOARD_EDGE_MINIMUM_FAMILY_SEGMENTS", 4
        ),
        board_edge_line_position_merge_distance_ratio=get_env_float(
            "ML_PREPROCESS_BOARD_EDGE_LINE_POSITION_MERGE_DISTANCE_RATIO", 0.03
        ),
        board_edge_minimum_distinct_lines_per_family=get_env_int(
            "ML_PREPROCESS_BOARD_EDGE_MINIMUM_DISTINCT_LINES_PER_FAMILY", 5
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
