from pydantic import BaseModel, ConfigDict, Field

from api.models.dataset_split_policy_api_entry import DatasetSplitPolicyApiEntry
from api.models.prepare_dataset_source_api_entry import (
    PrepareDatasetSourceApiEntry,
)


class PrepareDatasetArtifactApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    preparation_name: str = Field(alias="preparationName", min_length=1)
    dataset_name: str = Field(alias="datasetName", min_length=1)
    split_policy: DatasetSplitPolicyApiEntry = Field(alias="splitPolicy")
    sources: list[PrepareDatasetSourceApiEntry] = Field(min_length=1)
