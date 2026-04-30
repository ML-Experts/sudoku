from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from numpy.typing import NDArray
from torch.utils.data import Dataset

from application.features.trainings.errors.training_run_errors import (
    TrainingRunValidationError,
)
from infrastructure.training.data.input_transforms import InputTransform


@dataclass(frozen=True)
class NpzDigitArrays:
    x_train: NDArray[np.float32]
    y_train: NDArray[np.int64]
    x_val: NDArray[np.float32]
    y_val: NDArray[np.int64]
    x_test: NDArray[np.float32]
    y_test: NDArray[np.int64]
    class_names: tuple[str, ...]


class NpzDigitDataset(Dataset):
    def __init__(
        self,
        images: NDArray[np.float32],
        labels: NDArray[np.int64],
        transform: InputTransform,
    ) -> None:
        self._images = images
        self._labels = labels
        self._transform = transform

    def __len__(self) -> int:
        return int(self._labels.shape[0])

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        image = self._transform(self._images[index])
        label = torch.tensor(int(self._labels[index]), dtype=torch.long)
        return image, label


class NpzDigitDatasetLoader:
    _REQUIRED_KEYS = ("x_train", "y_train", "x_val", "y_val", "x_test", "y_test")

    def load(self, dataset_path: str) -> NpzDigitArrays:
        try:
            with np.load(Path(dataset_path), allow_pickle=False) as archive:
                missing_keys = [
                    key for key in self._REQUIRED_KEYS if key not in archive
                ]
                if missing_keys:
                    raise ValueError("missing npz keys")
                arrays = NpzDigitArrays(
                    x_train=archive["x_train"].astype(np.float32),
                    y_train=archive["y_train"].astype(np.int64),
                    x_val=archive["x_val"].astype(np.float32),
                    y_val=archive["y_val"].astype(np.int64),
                    x_test=archive["x_test"].astype(np.float32),
                    y_test=archive["y_test"].astype(np.int64),
                    class_names=tuple(
                        str(value)
                        for value in archive.get(
                            "class_names",
                            np.array([str(i) for i in range(10)]),
                        )
                    ),
                )
        except Exception as error:
            raise TrainingRunValidationError(
                "processed_dataset_invalid",
                "Plik .npz ma nieobsługiwany albo uszkodzony schemat.",
            ) from error

        self._validate_split(arrays.x_train, arrays.y_train, "train")
        self._validate_split(arrays.x_val, arrays.y_val, "val")
        self._validate_split(arrays.x_test, arrays.y_test, "test")
        if arrays.y_train.shape[0] == 0:
            raise TrainingRunValidationError(
                "processed_dataset_empty_train_split",
                "Split train w pliku .npz nie zawiera próbek.",
            )
        return arrays

    def _validate_split(
        self,
        images: NDArray[np.float32],
        labels: NDArray[np.int64],
        split_name: str,
    ) -> None:
        if images.shape[0] != labels.shape[0]:
            raise TrainingRunValidationError(
                "processed_dataset_invalid",
                f"Split {split_name} ma niespójne liczby obrazów i etykiet.",
            )
