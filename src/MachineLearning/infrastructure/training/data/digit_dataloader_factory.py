from torch.utils.data import DataLoader

from infrastructure.training.data.input_transforms import InputTransform
from infrastructure.training.data.npz_digit_dataset import (
    NpzDigitArrays,
    NpzDigitDataset,
)


class DigitDataloaderFactory:
    def build(
        self,
        arrays: NpzDigitArrays,
        transform: InputTransform,
        batch_size: int,
    ) -> dict[str, DataLoader]:
        return {
            "train": DataLoader(
                NpzDigitDataset(arrays.x_train, arrays.y_train, transform),
                batch_size=batch_size,
                shuffle=True,
            ),
            "val": DataLoader(
                NpzDigitDataset(arrays.x_val, arrays.y_val, transform),
                batch_size=batch_size,
                shuffle=False,
            ),
            "test": DataLoader(
                NpzDigitDataset(arrays.x_test, arrays.y_test, transform),
                batch_size=batch_size,
                shuffle=False,
            ),
        }
