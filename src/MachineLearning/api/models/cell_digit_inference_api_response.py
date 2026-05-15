from pydantic import BaseModel, ConfigDict, Field

from application.features.inference.commands.infer_cell_digit.infer_cell_digit_command_result_dto import (
    InferCellDigitCommandResultDto,
)


class CellDigitInferenceApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    digit: int | None = Field(default=None, ge=1, le=9)

    @classmethod
    def from_dto(
        cls,
        result: InferCellDigitCommandResultDto,
    ) -> "CellDigitInferenceApiResponse":
        return cls(digit=result.digit)
