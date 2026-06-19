from __future__ import annotations

from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np


def load_image_bgr(image_path: Path) -> np.ndarray:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")
    return image


def resize_for_display(image: np.ndarray, max_dimension: int) -> np.ndarray:
    height, width = image.shape[:2]
    longest_dimension = max(height, width)
    if longest_dimension <= max_dimension:
        return image.copy()

    scale = max_dimension / float(longest_dimension)
    resized_width = max(1, int(round(width * scale)))
    resized_height = max(1, int(round(height * scale)))
    return cv2.resize(
        image,
        (resized_width, resized_height),
        interpolation=cv2.INTER_AREA,
    )


def _to_rgb(image_bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)


def _is_valid_image(image: np.ndarray | None) -> bool:
    return image is not None and isinstance(image, np.ndarray) and image.size > 0


def plot_named_images(
    named_images: list[tuple[str, np.ndarray, bool]],
    *,
    columns: int = 3,
    figure_scale: float = 5.0,
) -> None:
    sanitized_named_images: list[tuple[str, np.ndarray, bool]] = []
    for title, image, is_bgr in named_images:
        if _is_valid_image(image):
            sanitized_named_images.append((title, image, is_bgr))
            continue

        placeholder = np.zeros((120, 320, 3), dtype=np.uint8)
        cv2.putText(
            placeholder,
            "Missing image",
            (18, 62),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        sanitized_named_images.append((f"{title} [missing]", placeholder, True))

    named_images = sanitized_named_images
    if not named_images:
        figure, axis = plt.subplots(figsize=(columns * figure_scale, figure_scale))
        axis.axis("off")
        axis.text(
            0.5,
            0.5,
            "No images to display.",
            ha="center",
            va="center",
            fontsize=14,
        )
        figure.tight_layout()
        plt.show()
        return

    rows = int(np.ceil(len(named_images) / columns))
    figure, axes = plt.subplots(
        rows,
        columns,
        figsize=(columns * figure_scale, rows * figure_scale),
    )
    axes_array = np.atleast_1d(axes).reshape(rows, columns)

    for axis in axes_array.flat:
        axis.axis("off")

    for axis, (title, image, is_bgr) in zip(axes_array.flat, named_images):
        display_image = _to_rgb(image) if is_bgr else image
        if not is_bgr and display_image.ndim == 2:
            axis.imshow(display_image, cmap="gray", vmin=0, vmax=255)
        else:
            axis.imshow(display_image)
        axis.set_title(title)
        axis.axis("off")

    figure.tight_layout()
    plt.show()


__all__ = [
    "load_image_bgr",
    "plot_named_images",
    "resize_for_display",
]
