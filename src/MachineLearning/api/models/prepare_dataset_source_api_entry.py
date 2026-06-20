from pydantic import BaseModel, ConfigDict, Field


class PrepareDatasetSourceApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    splits: list[str] = Field(min_length=1)
