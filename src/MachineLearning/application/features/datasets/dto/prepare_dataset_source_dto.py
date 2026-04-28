from dataclasses import dataclass

from application.features.datasets.dto.dataset_split_policy_dto import (
    DatasetSplitPolicyDto,
)


@dataclass(frozen=True)
class PrepareDatasetSourceDto:
    name: str
    type: str
    split_policy: DatasetSplitPolicyDto
