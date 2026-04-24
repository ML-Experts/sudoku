from pathlib import Path

import numpy as np
from numpy.typing import NDArray


class NpzDatasetArtifactWriter:
    def write(
        self,
        output_path: Path,
        x_train: NDArray[np.float32],
        y_train: NDArray[np.int64],
        x_val: NDArray[np.float32],
        y_val: NDArray[np.int64],
        x_test: NDArray[np.float32],
        y_test: NDArray[np.int64],
    ) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            output_path,
            x_train=x_train,
            y_train=y_train,
            x_val=x_val,
            y_val=y_val,
            x_test=x_test,
            y_test=y_test,
            class_names=np.array(
                ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
            ),
        )
