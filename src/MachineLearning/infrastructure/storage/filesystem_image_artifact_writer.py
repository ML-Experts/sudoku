from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.opencv_image_codec import OpenCvImageCodec


class FilesystemImageArtifactWriter:
    def __init__(
        self,
        image_codec: OpenCvImageCodec,
        output_mime_type: str = "image/png",
    ) -> None:
        self._image_codec = image_codec
        self._output_mime_type = output_mime_type

    def write(self, path: Path, image: NDArray[np.uint8]) -> None:
        encoded_image = self._image_codec.encode_image(
            image=image,
            mime_type=self._output_mime_type,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(f"{path.suffix}.tmp")
        temporary_path.write_bytes(encoded_image.image_bytes)
        temporary_path.replace(path)
