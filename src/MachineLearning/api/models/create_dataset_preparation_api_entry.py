from pydantic import BaseModel, ConfigDict, Field

from api.models.create_dataset_preparation_source_api_entry import (
    CreateDatasetPreparationSourceApiEntry,
)


class CreateDatasetPreparationApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    preparation_name: str = Field(alias="preparationName", min_length=1)
    sources: list[CreateDatasetPreparationSourceApiEntry] = Field(min_length=1)
