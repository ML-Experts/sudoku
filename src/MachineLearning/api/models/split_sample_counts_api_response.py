from pydantic import BaseModel, ConfigDict

from application.features.datasets.dto.split_sample_counts_dto import (
    SplitSampleCountsDto,
)


class SplitSampleCountsApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    train: int
    val: int
    test: int

    @classmethod
    def from_dto(
        cls, split_sample_counts: SplitSampleCountsDto
    ) -> "SplitSampleCountsApiResponse":
        return cls(
            train=split_sample_counts.train,
            val=split_sample_counts.val,
            test=split_sample_counts.test,
        )
