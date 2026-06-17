from __future__ import annotations

import cv2
import numpy as np

from models import ExperimentConfig


def _build_palette_color(
    index: int,
    count: int,
    hue_offset: int,
) -> tuple[int, int, int]:
    safe_count = max(1, count)
    hue = (hue_offset + int(round((160 * index) / safe_count))) % 180
    hsv_color = np.uint8([[[hue, 220, 255]]])
    bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0, 0]
    return int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2])


def _draw_label(
    image: np.ndarray,
    text: str,
    origin: tuple[int, int],
    color: tuple[int, int, int],
    config: ExperimentConfig,
) -> None:
    cv2.putText(
        image,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        config.axis_grid_label_font_scale,
        (0, 0, 0),
        config.axis_grid_label_thickness + 2,
        cv2.LINE_AA,
    )
    cv2.putText(
        image,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        config.axis_grid_label_font_scale,
        color,
        config.axis_grid_label_thickness,
        cv2.LINE_AA,
    )


def build_clean_binary_axis_overlay(
    binary_image: np.ndarray,
    config: ExperimentConfig,
) -> np.ndarray:
    if binary_image.ndim != 2:
        raise ValueError("build_clean_binary_axis_overlay expects a grayscale image.")

    image_height, image_width = binary_image.shape[:2]
    margin_left = config.axis_grid_margin_left_px
    margin_top = config.axis_grid_margin_top_px
    margin_right = config.axis_grid_margin_right_px
    margin_bottom = config.axis_grid_margin_bottom_px
    step_px = max(1, config.axis_grid_step_px)
    dot_radius = max(1, config.axis_grid_dot_radius)

    canvas_height = image_height + margin_top + margin_bottom
    canvas_width = image_width + margin_left + margin_right
    axis_overlay = np.full((canvas_height, canvas_width, 3), 255, dtype=np.uint8)

    binary_bgr = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    axis_overlay[
        margin_top : margin_top + image_height,
        margin_left : margin_left + image_width,
    ] = binary_bgr

    x_positions = list(range(0, image_width, step_px))
    y_positions = list(range(0, image_height, step_px))

    for x_index, x_position in enumerate(x_positions):
        line_color = _build_palette_color(x_index, len(x_positions), hue_offset=0)
        canvas_x = margin_left + x_position
        for y_position in y_positions:
            canvas_y = margin_top + y_position
            cv2.circle(
                axis_overlay,
                (canvas_x, canvas_y),
                dot_radius,
                line_color,
                thickness=-1,
                lineType=cv2.LINE_AA,
            )
        label_origin = (
            max(0, canvas_x - 11),
            max(12, margin_top - 6),
        )
        _draw_label(
            axis_overlay,
            str(x_position),
            label_origin,
            line_color,
            config,
        )

    for y_index, y_position in enumerate(y_positions):
        line_color = _build_palette_color(y_index, len(y_positions), hue_offset=90)
        canvas_y = margin_top + y_position
        for x_position in x_positions:
            canvas_x = margin_left + x_position
            cv2.circle(
                axis_overlay,
                (canvas_x, canvas_y),
                max(1, dot_radius - 1),
                line_color,
                thickness=-1,
                lineType=cv2.LINE_AA,
            )
        label_origin = (
            max(1, margin_left - 40),
            min(canvas_height - 4, canvas_y + 4),
        )
        _draw_label(
            axis_overlay,
            str(y_position),
            label_origin,
            line_color,
            config,
        )

    return axis_overlay


__all__ = ["build_clean_binary_axis_overlay"]
