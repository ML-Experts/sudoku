from __future__ import annotations

from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.engine_vision_pipeline import EngineVisionPipelineError


class BoardPreprocessingPipeline(Protocol):
    def preprocess_board(self, source_image: NDArray[np.uint8]) -> object: ...


class EngineBoardPreprocessor:
    def __init__(self, pipeline: BoardPreprocessingPipeline) -> None:
        self._pipeline = pipeline

    def preprocess(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        try:
            preprocess_result = self._pipeline.preprocess_board(image)
        except Exception as error:
            error_type = getattr(error, "error_type", None)
            if error_type == "board_not_found":
                raise EngineVisionPipelineError(
                    error_type="board_not_found",
                    message=str(error),
                ) from error
            raise EngineVisionPipelineError(
                error_type="perspective_correction_failed",
                message=str(error),
            ) from error

        return preprocess_result.warped_board_image
