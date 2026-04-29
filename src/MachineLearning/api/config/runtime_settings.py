from dataclasses import dataclass


@dataclass(frozen=True)
class PreprocessingSettings:
    allowed_input_mime_types: tuple[str, ...]
    board_output_mime_type: str
    board_output_size: int
    board_output_padding_pixels: int
    board_refinement_passes: int
    cells_grid_rows: int
    cells_grid_cols: int
    cells_inner_margin_ratio: float
    cells_minimum_cell_size_px: int
    cells_output_cell_size: int | None
    grayscale_color_conversion_code: int
    gaussian_kernel_size: tuple[int, int]
    gaussian_sigma_x: float
    adaptive_threshold_block_size: int
    adaptive_threshold_c: int
    board_edge_canny_threshold_1: int
    board_edge_canny_threshold_2: int
    board_edge_hough_threshold: int
    board_edge_min_line_length_ratio: float
    board_edge_max_line_gap_ratio: float
    board_edge_angle_tolerance_degrees: float
    board_edge_outer_line_window_ratio: float
    board_edge_minimum_board_area_ratio: float
    board_edge_minimum_family_segments: int
    board_edge_line_position_merge_distance_ratio: float
    board_edge_minimum_distinct_lines_per_family: int


@dataclass(frozen=True)
class TrainingSettings:
    runner: str
    backend_base_url: str
    event_timeout_seconds: float
    terminal_event_retry_delay_seconds: float
    terminal_event_max_attempts: int
    device: str
    max_epochs_override: int | None
    allowed_output_roots: tuple[str, ...]
    mock_interval_seconds: float
    active_event_max_attempts: int


@dataclass(frozen=True)
class RuntimeSettings:
    environment: str
    service_name: str
    service_version: str
    ping_response_message: str
    preprocessing_settings: PreprocessingSettings
    training_settings: TrainingSettings
    boards_subdirectory: str
    digits_subdirectory: str
    temp_datasets_directory_path: str
    examples_uploads_directory_path: str
    models_active_directory_path: str
    models_registry_directory_path: str
