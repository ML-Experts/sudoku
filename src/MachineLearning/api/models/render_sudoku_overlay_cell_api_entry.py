from pydantic import BaseModel, ConfigDict, Field

from api.models.image_api_entry import ImageApiEntry


class RenderSudokuOverlayCellApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    cell_image: ImageApiEntry = Field(alias="cellImage")
    digit: int
    row_index: int | None = Field(default=None, alias="rowIndex")
    column_index: int | None = Field(default=None, alias="columnIndex")
