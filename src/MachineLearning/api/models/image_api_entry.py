from pydantic import BaseModel, ConfigDict, Field


class ImageApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    mime_type: str = Field(alias="mimeType", min_length=1)
    base64: str = Field(min_length=1)
