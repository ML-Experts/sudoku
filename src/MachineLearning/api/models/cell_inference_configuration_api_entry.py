from pydantic import BaseModel, ConfigDict, Field


class CellInferenceConfigurationApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    inference_profile_name: str = Field(alias="inferenceProfileName", min_length=1)
    empty_cell_inner_margin_ratio: float = Field(
        alias="emptyCellInnerMarginRatio"
    )
    empty_cell_dark_pixel_ratio_threshold: float = Field(
        alias="emptyCellDarkPixelRatioThreshold"
    )
    center_area_ratio: float = Field(
        alias="centerAreaRatio"
    )
    min_component_area_ratio: float= Field(
        alias="minComponentAreaRatio"
    )
    line_artifact_min_span_ratio: float= Field(
        alias="lineArtifactMinSpanRatio"
    )
    line_artifact_max_thickness_ratio: float= Field(
        alias="lineArtifactMaxThicknessRatio"
    )
