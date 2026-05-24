from dataclasses import dataclass


@dataclass(frozen=True)
class InferenceRuntimeConfiguration:
    inference_profile_name: str
    empty_cell_inner_margin_ratio: float
    empty_cell_dark_pixel_ratio_threshold: float
    center_area_ratio: float
    min_component_area_ratio: float
    line_artifact_min_span_ratio: float
    line_artifact_max_thickness_ratio: float

    def __post_init__(self) -> None:
        if not self.inference_profile_name.strip():
            raise ValueError("Inference profile name is required.")
        if not 0.0 <= self.empty_cell_inner_margin_ratio < 0.5:
            raise ValueError(
                "Empty cell inner margin ratio must be in range [0.0, 0.5)."
            )
        if not 0.0 <= self.empty_cell_dark_pixel_ratio_threshold <= 1.0:
            raise ValueError(
                "Empty cell dark pixel ratio threshold must be in range [0.0, 1.0]."
            )

        if not 0.0 <= self.center_area_ratio <= 1.0:
            raise ValueError(
                "Center area ratio must be in range [0.0, 1.0]."
            )
        if not 0.0 <= self.min_component_area_ratio <= 1.0:
            raise ValueError(
                "Min component area ratio must be in range [0.0, 1.0]."
            )
