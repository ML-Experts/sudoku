from pydantic import BaseModel, ConfigDict, Field

from application.features.preprocessing.commands.preprocess_board.preprocess_board_command_result_dto import (
    PreprocessBoardCommandResultDto,
)


class ImageApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    mime_type: str = Field(alias="mimeType", min_length=1)
    base64: str = Field(min_length=1)

    @classmethod
    def from_dto(
        cls, preprocess_board_result: PreprocessBoardCommandResultDto
    ) -> "ImageApiResponse":
        return cls(
            mime_type=preprocess_board_result.mime_type,
            base64=preprocess_board_result.base64,
        )
