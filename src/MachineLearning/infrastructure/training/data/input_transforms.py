from collections.abc import Callable

import numpy as np
import torch
import torch.nn.functional as functional
from numpy.typing import NDArray


InputTransform = Callable[[NDArray[np.float32]], torch.Tensor]


class CnnInputTransform:
    def __call__(self, image: NDArray[np.float32]) -> torch.Tensor:
        tensor = torch.as_tensor(image, dtype=torch.float32)
        if tensor.max().item() > 1.0:
            tensor = tensor / 255.0
        if tensor.ndim == 2:
            tensor = tensor.unsqueeze(0)
        if tensor.ndim == 3 and tensor.shape[-1] == 1:
            tensor = tensor.permute(2, 0, 1)
        return tensor


class ResNetInputTransform:
    def __init__(self, height: int, width: int) -> None:
        self._height = height
        self._width = width

    def __call__(self, image: NDArray[np.float32]) -> torch.Tensor:
        tensor = CnnInputTransform()(image).unsqueeze(0)
        tensor = functional.interpolate(
            tensor,
            size=(self._height, self._width),
            mode="bilinear",
            align_corners=False,
        ).squeeze(0)
        if tensor.shape[0] == 1:
            tensor = tensor.repeat(3, 1, 1)
        return tensor
