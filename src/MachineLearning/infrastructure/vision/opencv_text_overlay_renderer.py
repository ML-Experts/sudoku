from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class _OverlayLayout:
    font_scale: float
    thickness: int
    origin: tuple[int, int]


@dataclass(frozen=True)
class _NormalizedCanvas:
    bgr_canvas: NDArray[np.uint8]
    original_mode: str
    alpha_channel: NDArray[np.uint8] | None = None


class OpenCvTextOverlayRenderer:
    _FONT_FACE = cv2.FONT_HERSHEY_SIMPLEX
    _FONT_SCALE_PADDING = 1.0
    _TARGET_TEXT_HEIGHT_RATIO = 0.55
    _TARGET_TEXT_WIDTH_RATIO = 0.55
    _MIN_MARGIN_RATIO = 0.1
    _LIGHT_TEXT_COLOR = (255, 255, 255)
    _DARK_TEXT_COLOR = (0, 0, 0)
    _MIN_CONTRAST_RATIO = 3.0
    _TEXT_ALPHA = 0.82
    _OUTLINE_ALPHA = 0.5

    def render_centered_text(
        self,
        image: NDArray[np.uint8],
        text: str,
    ) -> NDArray[np.uint8]:
        normalized_text = text.strip()
        if not normalized_text:
            raise ValueError("Overlay text must not be empty.")

        normalized_canvas = self._normalize_canvas(image)
        canvas = normalized_canvas.bgr_canvas.copy()
        layout = self._calculate_layout(
            text=normalized_text,
            canvas_height=canvas.shape[0],
            canvas_width=canvas.shape[1],
        )
        text_color, outline_color = self._select_overlay_colors(canvas)
        self._draw_text(
            canvas=canvas,
            text=normalized_text,
            layout=layout,
            text_color=text_color,
            outline_color=outline_color,
        )
        return self._restore_canvas_format(canvas, normalized_canvas)

    def _normalize_canvas(self, image: NDArray[np.uint8]) -> _NormalizedCanvas:
        if image.size == 0:
            raise ValueError("Overlay canvas must not be empty.")

        if image.ndim == 2:
            return _NormalizedCanvas(
                bgr_canvas=cv2.cvtColor(image.copy(), cv2.COLOR_GRAY2BGR),
                original_mode="gray",
            )

        if image.ndim != 3:
            raise ValueError("Overlay canvas must be 2D or 3D.")

        if image.shape[2] == 1:
            return _NormalizedCanvas(
                bgr_canvas=cv2.cvtColor(image[:, :, 0].copy(), cv2.COLOR_GRAY2BGR),
                original_mode="gray-single-channel",
            )

        if image.shape[2] == 3:
            return _NormalizedCanvas(
                bgr_canvas=image.copy(),
                original_mode="bgr",
            )

        if image.shape[2] == 4:
            alpha_channel = image[:, :, 3].copy()
            return _NormalizedCanvas(
                bgr_canvas=cv2.cvtColor(image.copy(), cv2.COLOR_BGRA2BGR),
                original_mode="bgra",
                alpha_channel=alpha_channel,
            )

        raise ValueError("Unsupported overlay canvas channel count.")

    def _calculate_layout(
        self,
        text: str,
        canvas_height: int,
        canvas_width: int,
    ) -> _OverlayLayout:
        if canvas_height <= 0 or canvas_width <= 0:
            raise ValueError("Overlay canvas dimensions must be positive.")

        target_width = max(
            1,
            int(round(canvas_width * self._TARGET_TEXT_WIDTH_RATIO)),
        )
        target_height = max(
            1,
            int(round(canvas_height * self._TARGET_TEXT_HEIGHT_RATIO)),
        )
        horizontal_margin = max(0, (canvas_width - target_width) // 2)
        vertical_margin = max(0, (canvas_height - target_height) // 2)
        minimum_margin = max(
            2,
            int(round(min(canvas_height, canvas_width) * self._MIN_MARGIN_RATIO)),
        )
        margin_px = max(horizontal_margin, vertical_margin, minimum_margin)
        max_text_width = max(canvas_width - (2 * margin_px), 1)
        max_text_height = max(canvas_height - (2 * margin_px), 1)

        base_size, _ = cv2.getTextSize(text, self._FONT_FACE, 1.0, 1)
        base_width = max(base_size[0], 1)
        base_height = max(base_size[1], 1)

        font_scale = min(
            max_text_width / base_width,
            max_text_height / base_height,
        ) * self._FONT_SCALE_PADDING
        font_scale = max(font_scale, 0.1)

        thickness = max(1, int(round(font_scale * 2.5)))
        text_size, baseline = cv2.getTextSize(
            text,
            self._FONT_FACE,
            font_scale,
            thickness,
        )

        while (
            (text_size[0] > max_text_width or text_size[1] > max_text_height)
            and font_scale > 0.1
        ):
            font_scale *= 0.9
            thickness = max(1, int(round(font_scale * 2.5)))
            text_size, baseline = cv2.getTextSize(
                text,
                self._FONT_FACE,
                font_scale,
                thickness,
            )

        origin_x = max(margin_px, (canvas_width - text_size[0]) // 2)
        origin_y = max(
            text_size[1] + margin_px,
            (canvas_height + text_size[1]) // 2 - (baseline // 2),
        )
        return _OverlayLayout(
            font_scale=font_scale,
            thickness=thickness,
            origin=(origin_x, origin_y),
        )

    def _select_overlay_colors(
        self,
        canvas: NDArray[np.uint8],
    ) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        background_color = self._estimate_background_color(canvas)
        preferred_text_color = tuple(255 - channel for channel in background_color)
        text_color = self._boost_text_contrast(
            background_color=background_color,
            preferred_text_color=preferred_text_color,
        )
        outline_color = self._select_outline_color(text_color)
        return text_color, outline_color

    def _estimate_background_color(
        self,
        canvas: NDArray[np.uint8],
    ) -> tuple[int, int, int]:
        height, width = canvas.shape[:2]
        border_band = max(
            1,
            int(round(min(height, width) * self._MIN_MARGIN_RATIO)),
        )

        top_band = canvas[:border_band, :, :]
        bottom_band = canvas[height - border_band :, :, :]
        left_band = canvas[:, :border_band, :]
        right_band = canvas[:, width - border_band :, :]
        border_pixels = np.concatenate(
            (
                top_band.reshape(-1, 3),
                bottom_band.reshape(-1, 3),
                left_band.reshape(-1, 3),
                right_band.reshape(-1, 3),
            ),
            axis=0,
        )
        estimated_background = np.median(border_pixels, axis=0)
        return tuple(int(channel) for channel in estimated_background)

    def _boost_text_contrast(
        self,
        background_color: tuple[int, int, int],
        preferred_text_color: tuple[int, int, int],
    ) -> tuple[int, int, int]:
        current_contrast = self._contrast_ratio(
            background_color,
            preferred_text_color,
        )
        if current_contrast >= self._MIN_CONTRAST_RATIO:
            return preferred_text_color

        light_contrast = self._contrast_ratio(
            background_color,
            self._LIGHT_TEXT_COLOR,
        )
        dark_contrast = self._contrast_ratio(
            background_color,
            self._DARK_TEXT_COLOR,
        )
        anchor_color = (
            self._LIGHT_TEXT_COLOR
            if light_contrast >= dark_contrast
            else self._DARK_TEXT_COLOR
        )

        for blend_ratio in np.linspace(0.15, 1.0, num=18):
            candidate_color = self._blend_colors(
                preferred_text_color,
                anchor_color,
                float(blend_ratio),
            )
            if (
                self._contrast_ratio(background_color, candidate_color)
                >= self._MIN_CONTRAST_RATIO
            ):
                return candidate_color

        return anchor_color

    def _select_outline_color(
        self,
        text_color: tuple[int, int, int],
    ) -> tuple[int, int, int]:
        text_luminance = self._relative_luminance(text_color)
        if text_luminance >= self._relative_luminance(self._LIGHT_TEXT_COLOR) / 2:
            return self._DARK_TEXT_COLOR
        return self._LIGHT_TEXT_COLOR

    def _blend_colors(
        self,
        start_color: tuple[int, int, int],
        target_color: tuple[int, int, int],
        blend_ratio: float,
    ) -> tuple[int, int, int]:
        clamped_ratio = min(max(blend_ratio, 0.0), 1.0)
        blended = []
        for start_channel, target_channel in zip(start_color, target_color):
            value = (
                ((1.0 - clamped_ratio) * start_channel)
                + (clamped_ratio * target_channel)
            )
            blended.append(int(round(value)))
        return tuple(blended)

    def _contrast_ratio(
        self,
        first_color: tuple[int, int, int],
        second_color: tuple[int, int, int],
    ) -> float:
        first_luminance = self._relative_luminance(first_color)
        second_luminance = self._relative_luminance(second_color)
        lighter = max(first_luminance, second_luminance)
        darker = min(first_luminance, second_luminance)
        return (lighter + 0.05) / (darker + 0.05)

    def _relative_luminance(
        self,
        color: tuple[int, int, int],
    ) -> float:
        blue, green, red = color
        normalized_channels = (
            self._to_linear_channel(red / 255.0),
            self._to_linear_channel(green / 255.0),
            self._to_linear_channel(blue / 255.0),
        )
        red_linear, green_linear, blue_linear = normalized_channels
        return (
            0.2126 * red_linear
            + 0.7152 * green_linear
            + 0.0722 * blue_linear
        )

    def _to_linear_channel(
        self,
        value: float,
    ) -> float:
        if value <= 0.04045:
            return value / 12.92
        return ((value + 0.055) / 1.055) ** 2.4

    def _draw_text(
        self,
        canvas: NDArray[np.uint8],
        text: str,
        layout: _OverlayLayout,
        text_color: tuple[int, int, int],
        outline_color: tuple[int, int, int],
    ) -> None:
        outline_thickness = max(layout.thickness + 2, layout.thickness * 2)
        outline_layer = canvas.copy()
        cv2.putText(
            outline_layer,
            text,
            layout.origin,
            self._FONT_FACE,
            layout.font_scale,
            outline_color,
            outline_thickness,
            cv2.LINE_AA,
        )
        self._blend_text_layer(
            canvas=canvas,
            overlay_layer=outline_layer,
            alpha=self._OUTLINE_ALPHA,
        )

        text_layer = canvas.copy()
        cv2.putText(
            text_layer,
            text,
            layout.origin,
            self._FONT_FACE,
            layout.font_scale,
            text_color,
            layout.thickness,
            cv2.LINE_AA,
        )
        self._blend_text_layer(
            canvas=canvas,
            overlay_layer=text_layer,
            alpha=self._TEXT_ALPHA,
        )

    def _blend_text_layer(
        self,
        canvas: NDArray[np.uint8],
        overlay_layer: NDArray[np.uint8],
        alpha: float,
    ) -> None:
        changed_mask = np.any(overlay_layer != canvas, axis=2)
        if not np.any(changed_mask):
            return

        base_pixels = canvas[changed_mask].astype(np.float32)
        overlay_pixels = overlay_layer[changed_mask].astype(np.float32)
        blended_pixels = (
            (alpha * overlay_pixels) + ((1.0 - alpha) * base_pixels)
        )
        canvas[changed_mask] = np.clip(blended_pixels, 0, 255).astype(np.uint8)

    def _restore_canvas_format(
        self,
        canvas: NDArray[np.uint8],
        normalized_canvas: _NormalizedCanvas,
    ) -> NDArray[np.uint8]:
        if normalized_canvas.original_mode in {"gray", "gray-single-channel"}:
            restored_gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
            if normalized_canvas.original_mode == "gray-single-channel":
                return restored_gray[:, :, np.newaxis]
            return restored_gray

        if normalized_canvas.original_mode == "bgra":
            restored = cv2.cvtColor(canvas, cv2.COLOR_BGR2BGRA)
            if normalized_canvas.alpha_channel is not None:
                restored[:, :, 3] = normalized_canvas.alpha_channel
            return restored

        return canvas
