from dataclasses import dataclass


@dataclass(frozen=True)
class PreprocessingSettings:
    allowed_input_mime_types: tuple[str, ...]
    board_output_mime_type: str
    board_output_size: int
    grayscale_color_conversion_code: int
    gaussian_kernel_size: tuple[int, int]
    gaussian_sigma_x: float
    adaptive_threshold_block_size: int
    adaptive_threshold_c: int
    contour_retrieval_mode: int
    contour_approximation_mode: int
    polygon_epsilon_factor: float


@dataclass(frozen=True)
class RuntimeSettings:
    environment: str
    service_name: str
    service_version: str
    ping_response_message: str
    preprocessing_settings: PreprocessingSettings
