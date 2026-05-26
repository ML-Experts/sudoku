from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def find_repo_root(start_path: Path | None = None) -> Path:
    current_path = (start_path or Path.cwd()).resolve()
    for candidate in [current_path, *current_path.parents]:
        if (candidate / ".git").exists() or (candidate / ".ai").exists():
            return candidate
    raise FileNotFoundError(
        "Could not locate repository root from the current working directory."
    )


REPO_ROOT = find_repo_root()
DRAFT_DIR = REPO_ROOT / "src" / "MachineLearning" / "draft"


@dataclass(slots=True)
class ExperimentConfig:
    dataset_root: Path = REPO_ROOT / "data" / "raw" / "boards"
    image_path: Path | None = None
    selected_dataset_index: int = 0
    preview_limit: int = 20
    max_display_size: int = 1600
    gaussian_kernel_size: tuple[int, int] = (5, 5)
    median_kernel_size: int = 5
    bilateral_diameter: int = 9
    bilateral_sigma_color: int = 75
    bilateral_sigma_space: int = 75
    nl_means_strength: int = 13
    nl_means_template_window_size: int = 7
    nl_means_search_window_size: int = 21
    adaptive_method_name: str = "gaussian"
    adaptive_block_sizes: tuple[int, ...] = (11, 15, 21, 31)
    adaptive_c_values: tuple[int, ...] = (2, 4, 6)
    threshold_invert: bool = True
    binary_min_component_area_ratio: float = 0.00008
    binary_min_component_area_floor_px: int = 16
    soft_cleanup_area_multiplier: float = 0.35
    repair_kernel_sizes: tuple[int, ...] = (3, 5)
    repair_directional_kernel_ratio: float = 0.015
    raw_hough_threshold: int = 35
    raw_min_line_length_ratio: float = 0.08
    raw_max_line_gap_ratio: float = 0.02
    line_family_angle_tolerance_degrees: float = 20.0
    horizontal_family_color_bgr: tuple[int, int, int] = (255, 165, 0)
    vertical_family_color_bgr: tuple[int, int, int] = (0, 255, 255)
    line_overlay_thickness: int = 2
    selected_denoise_variant: str = "median_5"
    selected_threshold_name: str | None = None
    selected_cleanup_variant: str | None = "adaptive_plus_components_soft"
    selected_repair_variant: str | None = "directional_close"


@dataclass(frozen=True)
class DetectedLineSegment:
    start: tuple[int, int]
    end: tuple[int, int]
    length: float
    angle_degrees: float


@dataclass(frozen=True)
class LineFamilyResult:
    raw_segment_count: int
    raw_min_line_length_px: int
    raw_max_line_gap_px: int
    horizontal_angle_degrees: float | None
    vertical_angle_degrees: float | None
    horizontal_segments: list[DetectedLineSegment]
    vertical_segments: list[DetectedLineSegment]


def discover_dataset_images(dataset_root: Path) -> list[Path]:
    if not dataset_root.exists():
        return []

    return sorted(
        path
        for path in dataset_root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def path_for_display(path: Path, base_path: Path) -> str:
    try:
        return str(path.relative_to(base_path))
    except ValueError:
        return str(path)


def resolve_active_image_path(config: ExperimentConfig) -> tuple[Path, list[Path]]:
    dataset_images = discover_dataset_images(config.dataset_root)

    if config.image_path is not None:
        image_path = config.image_path.resolve()
        if not image_path.exists():
            raise FileNotFoundError(f"Configured image does not exist: {image_path}")
        return image_path, dataset_images

    if not dataset_images:
        raise FileNotFoundError(
            "No dataset images found. Set CONFIG.dataset_root or CONFIG.image_path first."
        )

    selected_index = max(0, min(config.selected_dataset_index, len(dataset_images) - 1))
    return dataset_images[selected_index], dataset_images


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


def to_rgb(image_bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)


def plot_named_images(
    named_images: list[tuple[str, np.ndarray, bool]],
    *,
    columns: int = 3,
    figure_scale: float = 5.0,
) -> None:
    if not named_images:
        raise ValueError("No images to display.")

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
        display_image = to_rgb(image) if is_bgr else image
        axis.imshow(display_image)
        axis.set_title(title)
        axis.axis("off")

    figure.tight_layout()
    plt.show()


def build_denoise_variants(
    gray_image: np.ndarray,
    config: ExperimentConfig,
) -> dict[str, np.ndarray]:
    return {
        "raw_gray": gray_image,
        f"gaussian_{config.gaussian_kernel_size[0]}": cv2.GaussianBlur(
            gray_image,
            config.gaussian_kernel_size,
            0,
        ),
        f"median_{config.median_kernel_size}": cv2.medianBlur(
            gray_image,
            config.median_kernel_size,
        ),
        "bilateral": cv2.bilateralFilter(
            gray_image,
            config.bilateral_diameter,
            config.bilateral_sigma_color,
            config.bilateral_sigma_space,
        ),
        "nl_means": cv2.fastNlMeansDenoising(
            gray_image,
            None,
            h=config.nl_means_strength,
            templateWindowSize=config.nl_means_template_window_size,
            searchWindowSize=config.nl_means_search_window_size,
        ),
    }


def adaptive_method_code(method_name: str) -> int:
    normalized_method_name = method_name.strip().lower()
    if normalized_method_name == "mean":
        return cv2.ADAPTIVE_THRESH_MEAN_C
    if normalized_method_name == "gaussian":
        return cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    raise ValueError(f"Unsupported adaptive method: {method_name}")


def build_threshold_variants(
    denoised_image: np.ndarray,
    config: ExperimentConfig,
) -> dict[str, np.ndarray]:
    threshold_variants: dict[str, np.ndarray] = {}
    method_code = adaptive_method_code(config.adaptive_method_name)
    threshold_type = (
        cv2.THRESH_BINARY_INV if config.threshold_invert else cv2.THRESH_BINARY
    )

    for block_size in config.adaptive_block_sizes:
        if block_size % 2 == 0:
            raise ValueError(f"Adaptive block size must be odd: {block_size}")

        for c_value in config.adaptive_c_values:
            variant_name = f"{config.adaptive_method_name}_block{block_size}_c{c_value}"
            threshold_variants[variant_name] = cv2.adaptiveThreshold(
                denoised_image,
                255,
                method_code,
                threshold_type,
                block_size,
                c_value,
            )

    return threshold_variants


def resolve_min_component_area_px(
    binary_image: np.ndarray,
    config: ExperimentConfig,
) -> int:
    minimum_dimension = min(binary_image.shape[:2])
    return max(
        config.binary_min_component_area_floor_px,
        int(
            round(
                minimum_dimension
                * minimum_dimension
                * config.binary_min_component_area_ratio
            )
        ),
    )


def remove_small_connected_components(
    binary_image: np.ndarray,
    min_area_px: int,
) -> np.ndarray:
    component_count, component_labels, component_stats, _ = (
        cv2.connectedComponentsWithStats(
            binary_image,
            connectivity=8,
        )
    )
    cleaned = np.zeros_like(binary_image)
    for component_index in range(1, component_count):
        component_area = component_stats[component_index, cv2.CC_STAT_AREA]
        if component_area >= min_area_px:
            cleaned[component_labels == component_index] = 255
    return cleaned


def build_cleanup_variants(
    binary_image: np.ndarray,
    config: ExperimentConfig,
) -> tuple[int, dict[str, np.ndarray]]:
    min_component_area_px = resolve_min_component_area_px(binary_image, config)
    soft_min_component_area_px = max(
        1,
        int(round(min_component_area_px * config.soft_cleanup_area_multiplier)),
    )
    cleanup_variants = {
        "adaptive_only": binary_image,
        "adaptive_plus_components_soft": remove_small_connected_components(
            binary_image,
            soft_min_component_area_px,
        ),
        "adaptive_plus_components": remove_small_connected_components(
            binary_image,
            min_component_area_px,
        ),
    }
    return min_component_area_px, cleanup_variants


def close_binary_image(
    binary_image: np.ndarray,
    kernel_size: tuple[int, int],
) -> np.ndarray:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    return cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)


def build_repair_variants(
    binary_image: np.ndarray,
    config: ExperimentConfig,
) -> dict[str, np.ndarray]:
    minimum_dimension = min(binary_image.shape[:2])
    directional_kernel_length = max(
        3,
        int(round(minimum_dimension * config.repair_directional_kernel_ratio)),
    )
    if directional_kernel_length % 2 == 0:
        directional_kernel_length += 1

    repair_variants = {"cleanup_only": binary_image}
    for kernel_size in config.repair_kernel_sizes:
        repair_variants[f"close_square_{kernel_size}"] = close_binary_image(
            binary_image,
            (kernel_size, kernel_size),
        )

    horizontal_closed = close_binary_image(binary_image, (directional_kernel_length, 1))
    vertical_closed = close_binary_image(binary_image, (1, directional_kernel_length))
    repair_variants["directional_close"] = cv2.bitwise_or(
        horizontal_closed,
        vertical_closed,
    )
    return repair_variants


def build_line_segment(raw_segment: np.ndarray) -> DetectedLineSegment:
    x1, y1, x2, y2 = (int(value) for value in raw_segment)
    delta_x = float(x2 - x1)
    delta_y = float(y2 - y1)
    return DetectedLineSegment(
        start=(x1, y1),
        end=(x2, y2),
        length=float(np.hypot(delta_x, delta_y)),
        angle_degrees=float(np.degrees(np.arctan2(delta_y, delta_x)) % 180.0),
    )


def angle_difference_degrees(first_angle: float, second_angle: float) -> float:
    raw_difference = abs(first_angle - second_angle) % 180.0
    return min(raw_difference, 180.0 - raw_difference)


def get_dominant_angle_degrees(
    line_segments: list[DetectedLineSegment],
) -> float | None:
    if not line_segments:
        return None

    angle_histogram = np.zeros(180, dtype=np.float32)
    for line_segment in line_segments:
        angle_bucket = int(round(line_segment.angle_degrees)) % 180
        angle_histogram[angle_bucket] += line_segment.length
    return float(np.argmax(angle_histogram))


def collect_line_family(
    line_segments: list[DetectedLineSegment],
    target_angle_degrees: float,
    angle_tolerance_degrees: float,
) -> list[DetectedLineSegment]:
    return [
        line_segment
        for line_segment in line_segments
        if angle_difference_degrees(
            line_segment.angle_degrees,
            target_angle_degrees,
        )
        <= angle_tolerance_degrees
    ]


def is_horizontal_like(angle_degrees: float) -> bool:
    return angle_difference_degrees(angle_degrees, 0.0) <= angle_difference_degrees(
        angle_degrees,
        90.0,
    )


def detect_line_families(
    binary_image: np.ndarray,
    config: ExperimentConfig,
) -> LineFamilyResult:
    minimum_dimension = min(binary_image.shape[:2])
    raw_min_line_length_px = max(
        8,
        int(round(minimum_dimension * config.raw_min_line_length_ratio)),
    )
    raw_max_line_gap_px = max(
        2,
        int(round(minimum_dimension * config.raw_max_line_gap_ratio)),
    )

    raw_segments = cv2.HoughLinesP(
        binary_image,
        rho=1,
        theta=np.pi / 180.0,
        threshold=config.raw_hough_threshold,
        minLineLength=raw_min_line_length_px,
        maxLineGap=raw_max_line_gap_px,
    )
    if raw_segments is None:
        return LineFamilyResult(
            raw_segment_count=0,
            raw_min_line_length_px=raw_min_line_length_px,
            raw_max_line_gap_px=raw_max_line_gap_px,
            horizontal_angle_degrees=None,
            vertical_angle_degrees=None,
            horizontal_segments=[],
            vertical_segments=[],
        )

    line_segments = [build_line_segment(raw_segment[0]) for raw_segment in raw_segments]
    primary_angle = get_dominant_angle_degrees(line_segments)
    if primary_angle is None:
        return LineFamilyResult(
            raw_segment_count=0,
            raw_min_line_length_px=raw_min_line_length_px,
            raw_max_line_gap_px=raw_max_line_gap_px,
            horizontal_angle_degrees=None,
            vertical_angle_degrees=None,
            horizontal_segments=[],
            vertical_segments=[],
        )

    primary_segments = collect_line_family(
        line_segments,
        primary_angle,
        config.line_family_angle_tolerance_degrees,
    )
    remaining_segments = [
        line_segment
        for line_segment in line_segments
        if angle_difference_degrees(
            line_segment.angle_degrees,
            primary_angle,
        )
        > config.line_family_angle_tolerance_degrees
    ]

    secondary_angle = get_dominant_angle_degrees(remaining_segments)
    if secondary_angle is None:
        secondary_angle = (primary_angle + 90.0) % 180.0
    secondary_segments = collect_line_family(
        line_segments,
        secondary_angle,
        config.line_family_angle_tolerance_degrees,
    )

    if is_horizontal_like(primary_angle):
        horizontal_angle_degrees = primary_angle
        horizontal_segments = primary_segments
        vertical_angle_degrees = secondary_angle
        vertical_segments = secondary_segments
    else:
        horizontal_angle_degrees = secondary_angle
        horizontal_segments = secondary_segments
        vertical_angle_degrees = primary_angle
        vertical_segments = primary_segments

    return LineFamilyResult(
        raw_segment_count=len(line_segments),
        raw_min_line_length_px=raw_min_line_length_px,
        raw_max_line_gap_px=raw_max_line_gap_px,
        horizontal_angle_degrees=horizontal_angle_degrees,
        vertical_angle_degrees=vertical_angle_degrees,
        horizontal_segments=horizontal_segments,
        vertical_segments=vertical_segments,
    )


def build_line_family_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: LineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()

    for overlay in (binary_overlay, source_overlay):
        for line_segment in line_family_result.horizontal_segments:
            cv2.line(
                overlay,
                line_segment.start,
                line_segment.end,
                config.horizontal_family_color_bgr,
                config.line_overlay_thickness,
                cv2.LINE_AA,
            )
        for line_segment in line_family_result.vertical_segments:
            cv2.line(
                overlay,
                line_segment.start,
                line_segment.end,
                config.vertical_family_color_bgr,
                config.line_overlay_thickness,
                cv2.LINE_AA,
            )

    return binary_overlay, source_overlay


__all__ = [
    "DRAFT_DIR",
    "REPO_ROOT",
    "DetectedLineSegment",
    "ExperimentConfig",
    "IMAGE_EXTENSIONS",
    "LineFamilyResult",
    "adaptive_method_code",
    "angle_difference_degrees",
    "build_cleanup_variants",
    "build_denoise_variants",
    "build_line_family_overlays",
    "build_repair_variants",
    "build_threshold_variants",
    "close_binary_image",
    "collect_line_family",
    "detect_line_families",
    "discover_dataset_images",
    "find_repo_root",
    "get_dominant_angle_degrees",
    "load_image_bgr",
    "path_for_display",
    "plot_named_images",
    "remove_small_connected_components",
    "resolve_active_image_path",
    "resolve_min_component_area_px",
    "resize_for_display",
    "to_rgb",
]
