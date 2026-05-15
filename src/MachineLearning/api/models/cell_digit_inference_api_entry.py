from pydantic import BaseModel, ConfigDict, Field

from api.models.active_model_reference_api_entry import (
    ActiveModelReferenceApiEntry,
)
from api.models.cell_inference_configuration_api_entry import (
    CellInferenceConfigurationApiEntry,
)
from api.models.image_api_entry import ImageApiEntry


class CellDigitInferenceApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    image: ImageApiEntry
    active_model: ActiveModelReferenceApiEntry = Field(alias="activeModel")
    resolved_configuration: CellInferenceConfigurationApiEntry = Field(
        alias="resolvedConfiguration"
    )
