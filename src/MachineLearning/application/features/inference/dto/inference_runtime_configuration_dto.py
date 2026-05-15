from dataclasses import dataclass


@dataclass(frozen=True)
class InferenceRuntimeConfigurationDto:
    inference_profile_name: str
    empty_cell_inner_margin_ratio: float
    empty_cell_dark_pixel_ratio_threshold: float
