import hashlib

from application.features.datasets.dto.dataset_split_policy_dto import (
    DatasetSplitPolicyDto,
)
from models.dataset_split import DatasetSplit


class SampleSplitAssigner:
    def assign_split(
        self, split_policy: DatasetSplitPolicyDto, stable_key: str
    ) -> DatasetSplit:
        ratios = split_policy.ratios
        bucket = self._deterministic_bucket(stable_key)

        train_limit = ratios.train
        val_limit = ratios.train + ratios.val

        if bucket < train_limit:
            return DatasetSplit.TRAIN
        if bucket < val_limit:
            return DatasetSplit.VAL
        return DatasetSplit.TEST

    def _deterministic_bucket(self, stable_key: str) -> float:
        key_hash = hashlib.sha1(stable_key.encode("utf-8")).hexdigest()
        numeric = int(key_hash[:8], 16)
        return numeric / 0xFFFFFFFF
