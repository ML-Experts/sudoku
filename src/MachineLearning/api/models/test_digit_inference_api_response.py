from pydantic import BaseModel, ConfigDict, Field

from application.features.inference.dto.test_digit_inference_result_dto import (
    TestDigitInferenceResultDto,
)


class TestDigitInferenceApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    digit: int = Field(ge=0, le=9)

    @classmethod
    def from_dto(
        cls,
        result: TestDigitInferenceResultDto,
    ) -> "TestDigitInferenceApiResponse":
        return cls(digit=result.digit)
