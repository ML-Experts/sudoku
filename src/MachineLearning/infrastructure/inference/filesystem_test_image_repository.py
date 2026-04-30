from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from application.features.inference.errors.test_digit_inference_errors import (
    TestDigitInferenceCommandError,
)


class FilesystemTestImageRepository:
    _DEFAULT_EXTENSIONS = (".png", ".jpg", ".jpeg")

    def __init__(self, directory_path: str) -> None:
        self._directory_path = Path(directory_path)

    def load(self, image_name: str) -> NDArray[np.uint8]:
        image_path = self._resolve_image_path(image_name)
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise TestDigitInferenceCommandError(
                status_code=422,
                error_type="test_image_invalid",
                message="Nie udało się odczytać obrazka testowego.",
            )
        return image

    def _resolve_image_path(self, image_name: str) -> Path:
        if not image_name or Path(image_name).name != image_name:
            raise TestDigitInferenceCommandError(
                status_code=422,
                error_type="invalid_test_image_name",
                message="Nazwa obrazka testowego jest niepoprawna.",
            )

        requested_path = self._directory_path / image_name
        candidates = [requested_path]
        if requested_path.suffix == "":
            candidates = [
                self._directory_path / f"{image_name}{extension}"
                for extension in self._DEFAULT_EXTENSIONS
            ]

        for candidate in candidates:
            if candidate.is_file():
                return candidate

        raise TestDigitInferenceCommandError(
            status_code=404,
            error_type="test_image_not_found",
            message="Nie znaleziono obrazka testowego w domyślnym katalogu.",
        )
