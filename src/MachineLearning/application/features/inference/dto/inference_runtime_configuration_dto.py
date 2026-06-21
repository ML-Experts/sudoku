from dataclasses import dataclass


@dataclass(frozen=True)
class InferenceRuntimeConfigurationDto:
    inference_profile_name: str
    empty_cell_inner_margin_ratio: float
    empty_cell_dark_pixel_ratio_threshold: float
    center_area_ratio: float
    min_component_area_ratio: float
    line_artifact_min_span_ratio: float
    line_artifact_max_thickness_ratio: float
    empty_cell_min_segment_length_px: int
    empty_cell_filtered_segment_count_threshold: int

