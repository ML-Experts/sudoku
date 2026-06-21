import base64

import cv2
import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.engine.preprocessing_api_codec import normalize_mime_type
from models.preprocessing_image import PreprocessingImage


class VisionImageCodec:
    def decode_base64_image(
        self, base64_image: str, mime_type: str
    ) -> PreprocessingImage:
        normalized_mime_type = normalize_mime_type(mime_type)
        try:
            image_bytes = base64.b64decode(base64_image, validate=True)
        except ValueError as error:
            raise ValueError("Invalid base64 payload.") from error

        if not image_bytes:
            raise ValueError("Decoded image payload is empty.")

        return PreprocessingImage(
            mime_type=normalized_mime_type,
            image_bytes=image_bytes,
        )

    def decode_image(self, image: PreprocessingImage) -> NDArray[np.uint8]:
        image_array = np.frombuffer(image.image_bytes, dtype=np.uint8)
        decoded_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if decoded_image is None or decoded_image.size == 0:
            raise ValueError("OpenCV failed to decode image bytes.")

        return decoded_image

    def encode_image(
        self, image: NDArray[np.uint8], mime_type: str
    ) -> PreprocessingImage:
        normalized_mime_type = normalize_mime_type(mime_type)
        extension = ".jpg" if normalized_mime_type in {"image/jpeg", "image/jpg"} else {
            "image/png": ".png",
            "image/webp": ".webp",
        }.get(normalized_mime_type)
        if extension is None:
            raise ValueError(f"Unsupported mime type: {mime_type}")

        success, encoded = cv2.imencode(extension, image)
        if not success:
            raise ValueError("OpenCV failed to encode image.")

        return PreprocessingImage(
            mime_type=normalized_mime_type,
            image_bytes=encoded.tobytes(),
        )

    def encode_to_base64(self, image: PreprocessingImage) -> str:
        return base64.b64encode(image.image_bytes).decode("ascii")
