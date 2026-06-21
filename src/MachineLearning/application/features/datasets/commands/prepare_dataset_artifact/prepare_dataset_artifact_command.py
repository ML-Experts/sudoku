from dataclasses import dataclass

from application.features.datasets.dto.dataset_split_policy_dto import (
    DatasetSplitPolicyDto,
)
from application.features.datasets.dto.prepare_dataset_source_dto import (
    PrepareDatasetSourceDto,
)


@dataclass(frozen=True)
class PrepareDatasetArtifactCommand:
    preparation_name: str
    dataset_name: str
    split_policy: DatasetSplitPolicyDto
    sources: tuple[PrepareDatasetSourceDto, ...]
