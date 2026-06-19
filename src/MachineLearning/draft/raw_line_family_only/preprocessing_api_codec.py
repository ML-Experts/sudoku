from __future__ import annotations

import base64

import cv2
import numpy as np

from preprocessing_api_models import ImageApiEntry, ImageApiResponse


MIME_TYPE_TO_EXTENSION = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
}


def normalize_mime_type(mime_type: str) -> str:
    normalized_mime_type = mime_type.strip().lower()
    if not normalized_mime_type:
        raise ValueError("mime_type cannot be empty.")
    if normalized_mime_type not in MIME_TYPE_TO_EXTENSION:
        raise ValueError(f"Unsupported mime type: {mime_type}")
    return normalized_mime_type


def decode_image_api_entry(
    image_entry: ImageApiEntry,
) -> np.ndarray:
    return decode_base64_image(
        base64_payload=image_entry.base64,
        mime_type=image_entry.mime_type,
    )


def decode_base64_image(
    base64_payload: str,
    mime_type: str,
) -> np.ndarray:
    normalize_mime_type(mime_type)
    try:
        image_bytes = base64.b64decode(base64_payload, validate=True)
    except ValueError as error:
        raise ValueError("Invalid base64 payload.") from error

    if not image_bytes:
        raise ValueError("Decoded image payload is empty.")

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    decoded_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if decoded_image is None or decoded_image.size == 0:
        raise ValueError("OpenCV failed to decode image bytes.")

    return decoded_image


def encode_image_api_response(
    image: np.ndarray,
    mime_type: str,
) -> ImageApiResponse:
    normalized_mime_type = normalize_mime_type(mime_type)
    encoded_base64 = encode_image_to_base64(
        image=image,
        mime_type=normalized_mime_type,
    )
    return ImageApiResponse(
        mime_type=normalized_mime_type,
        base64=encoded_base64,
    )


def encode_image_to_base64(
    image: np.ndarray,
    mime_type: str,
) -> str:
    if image.size == 0:
        raise ValueError("Image cannot be empty.")

    normalized_mime_type = normalize_mime_type(mime_type)
    extension = MIME_TYPE_TO_EXTENSION[normalized_mime_type]
    success, encoded_buffer = cv2.imencode(extension, image)
    if not success:
        raise ValueError("OpenCV failed to encode image.")

    return base64.b64encode(encoded_buffer.tobytes()).decode("ascii")


__all__ = [
    "MIME_TYPE_TO_EXTENSION",
    "decode_base64_image",
    "decode_image_api_entry",
    "encode_image_api_response",
    "encode_image_to_base64",
    "normalize_mime_type",
]
