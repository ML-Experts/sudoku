from pydantic import BaseModel, ConfigDict, Field

from api.models.split_ratios_api_entry import SplitRatiosApiEntry


class DatasetSplitPolicyApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    mode: str = Field(min_length=1)
    ratios: SplitRatiosApiEntry
    group_by: str = Field(alias="groupBy", min_length=1)
