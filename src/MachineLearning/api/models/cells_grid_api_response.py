from pydantic import BaseModel, ConfigDict

from api.models.image_api_response import ImageApiResponse
from application.features.preprocessing.commands.extract_cells.extract_cells_command_result_dto import (
    ExtractCellsCommandResultDto,
)


class CellsGridApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    cells: list[list[ImageApiResponse]]

    @classmethod
    def from_dto(
        cls, extract_cells_result: ExtractCellsCommandResultDto
    ) -> "CellsGridApiResponse":
        return cls(
            cells=[
                [
                    ImageApiResponse(
                        mime_type=cell.mime_type,
                        base64=cell.base64,
                    )
                    for cell in row
                ]
                for row in extract_cells_result.cells
            ]
        )
