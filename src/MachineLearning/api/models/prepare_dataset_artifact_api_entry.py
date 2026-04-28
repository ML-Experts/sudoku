from pydantic import BaseModel, ConfigDict, Field

from api.models.prepare_dataset_source_api_entry import (
    PrepareDatasetSourceApiEntry,
)


class PrepareDatasetArtifactApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    dataset_name: str = Field(alias="datasetName", min_length=1)
    sources: list[PrepareDatasetSourceApiEntry] = Field(min_length=1)
    preprocessing_profile: str = Field(alias="preprocessingProfile", min_length=1)
