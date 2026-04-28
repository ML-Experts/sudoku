from pydantic import BaseModel, ConfigDict, Field


class SplitRatiosApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    train: float = Field(ge=0.0, le=1.0)
    val: float = Field(ge=0.0, le=1.0)
    test: float = Field(ge=0.0, le=1.0)
