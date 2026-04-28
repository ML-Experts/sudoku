from pydantic import BaseModel, ConfigDict, Field

from api.models.dataset_split_policy_api_entry import DatasetSplitPolicyApiEntry


class PrepareDatasetSourceApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    split_policy: DatasetSplitPolicyApiEntry = Field(alias="splitPolicy")
