from pydantic import BaseModel, ConfigDict, Field


class ErrorApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    error_type: str = Field(alias="errorType", min_length=1)
    message: str = Field(min_length=1)
