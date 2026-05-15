from dataclasses import dataclass


@dataclass(frozen=True)
class InferenceRuntimeConfiguration:
    inference_profile_name: str
    empty_cell_inner_margin_ratio: float
    empty_cell_dark_pixel_ratio_threshold: float

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
