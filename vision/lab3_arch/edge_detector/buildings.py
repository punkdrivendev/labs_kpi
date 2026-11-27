"""Classical building detection on RGB map images."""

from dataclasses import dataclass
from math import pi

import cv2
import numpy as np

from edge_detector.detector import detect_edges
from edge_detector.road_zones import Zone, assign_buildings, draw_road_separators, draw_zones, partition_zones
from image_processing.processing import image_to_grey, preprocess_image


HSV_SEGMENTATION = "HSV Segmentation"
GRAYSCALE_CANNY = "Grayscale + Canny"
COMBINED_DETECTION = "Combined Detection"
DETECTION_METHODS = (HSV_SEGMENTATION, GRAYSCALE_CANNY, COMBINED_DETECTION)
FINAL_STAGE = "Building contours"
HSV_OVERLAY_STAGE = "HSV exclusion overlay"
ZONES_STAGE = "Roads and zones"

HSVRange = tuple[tuple[int, int, int], tuple[int, int, int]]


@dataclass(frozen=True)
class DetectionSettings:
    preprocessing: tuple[int, float, int] = (0, 1.0, 5)
    hsv_ranges: tuple[HSVRange, ...] = (((30, 35, 20), (95, 255, 255)),)
    exclude_asphalt: bool = False
    asphalt_range: HSVRange = ((0, 0, 35), (179, 40, 155))
    hsv_boundary_margin: int = 1
    canny_thresholds: tuple[int, int] = (110, 220)
    opening_kernel: int | None = None
    closing_kernel: int = 3
    min_area: float | None = 40.0
    max_area_percent: float | None = 10.0
    max_aspect_ratio: float | None = 8.0
    min_compactness: float | None = 0.08
    min_solidity: float | None = None
    approximation_percent: float = 1.0
    roof_hsv_ranges: tuple[HSVRange, ...] = (
        ((0, 0, 108), (179, 32, 235)),
        ((165, 60, 95), (179, 255, 255)),
        ((0, 60, 95), (12, 255, 255)),
    )
    road_zones: bool = False
    min_zone_area: int = 10000
    road_separators: tuple[tuple[tuple[float, float], ...], ...] = ()


@dataclass
class DetectionResult:
    contours: list[np.ndarray]
    stages: dict[str, np.ndarray]
    counts: dict[str, int]
    zones: list[Zone] | None = None

    @property
    def count(self):
        return len(self.contours)


def validate_hsv_range(lower, upper):
    limits = (179, 255, 255)
    if len(lower) != 3 or len(upper) != 3 or any(
        not 0 <= lo <= hi <= limit for lo, hi, limit in zip(lower, upper, limits)
    ):
        raise ValueError("Use increasing HSV bounds in H 0–179, S/V 0–255.")


def _hsv_range_mask(hsv, ranges):
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lower, upper in ranges:
        validate_hsv_range(lower, upper)
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower, upper))
    return mask


def hsv_exclusion_overlay(image, mask):
    overlay = image.copy()
    selected = mask != 0
    overlay[selected] = (image[selected] * 0.45 + np.array((255, 40, 170)) * 0.55).astype(np.uint8)
    return overlay


def _candidate_mask(image, method, settings, stages):
    if method != GRAYSCALE_CANNY:
        ranges = settings.hsv_ranges
        if settings.exclude_asphalt:
            ranges = (*ranges, settings.asphalt_range)
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        excluded = _hsv_range_mask(hsv, ranges)
        stages["HSV exclusion mask"] = excluded
        if method == COMBINED_DETECTION:
            margin = settings.hsv_boundary_margin
            if not 0 <= margin <= 20:
                raise ValueError("HSV boundary margin must be between 0 and 20 pixels.")
            if margin:
                size = 2 * margin + 1
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
                excluded = cv2.erode(excluded, kernel)
                stages["HSV exclusion after margin"] = excluded
        allowed = cv2.bitwise_not(excluded)
        stages[HSV_OVERLAY_STAGE] = hsv_exclusion_overlay(image, excluded)
        stages["HSV retained areas"] = allowed
        if method == HSV_SEGMENTATION:
            if settings.roof_hsv_ranges:
                roof_colors = _hsv_range_mask(hsv, settings.roof_hsv_ranges)
                candidates = cv2.bitwise_and(roof_colors, allowed)
                stages["HSV roof candidates"] = candidates
                return candidates
            return allowed

    lower, upper = settings.canny_thresholds
    if not 0 <= lower < upper:
        raise ValueError("The lower Canny threshold must be below the upper threshold.")
    gray = image_to_grey(image)
    processed = preprocess_image(gray, *settings.preprocessing)
    edges = detect_edges(processed, lower, upper)
    stages["Grayscale"] = gray
    stages["Preprocessed grayscale"] = processed
    stages["Canny"] = edges
    if method == GRAYSCALE_CANNY:
        return edges

    combined = cv2.bitwise_and(edges, allowed)
    stages["Combined mask"] = combined
    return combined


def _find_contours(mask):
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    parents = hierarchy[0, :, 3] if hierarchy is not None else ()
    return contours, parents


def resolve_opening_kernel(method, kernel_size):
    if kernel_size is None:
        return 7 if method == HSV_SEGMENTATION else 1
    return kernel_size


def _morphology(mask, operation, kernel_size):
    if kernel_size < 1 or kernel_size % 2 == 0:
        raise ValueError("Morphology kernels must be positive odd sizes (1 disables the step).")
    if kernel_size == 1:
        return mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    return cv2.morphologyEx(mask, operation, kernel)


def _ancestors(index, parents):
    parent = parents[index]
    while parent != -1:
        yield parent
        parent = parents[parent]


def _aspect_ratio(contour):
    _, (width, height), _ = cv2.minAreaRect(contour)
    short_side = min(width, height)
    return max(width, height) / short_side if short_side > 0 else float("inf")


def _compactness(contour, area):
    perimeter = cv2.arcLength(contour, True)
    return 4 * pi * area / perimeter ** 2 if perimeter > 0 else 0.0


def _solidity(contour, area):
    hull_area = cv2.contourArea(cv2.convexHull(contour))
    return area / hull_area if hull_area > 0 else 0.0


def _filter_contours(contours, parents, method, settings, image_area, counts):
    areas = [cv2.contourArea(contour) for contour in contours]
    indices = [index for index, area in enumerate(areas) if area > 0]
    counts["Non-degenerate contours"] = len(indices)
    # With area masks, holes are excluded colors. With edge masks, a hole
    # represents an enclosed interior rather than the thickness of an open stroke.
    if method == HSV_SEGMENTATION:
        depth_parity, stage = 0, "HSV foreground contours"
    else:
        depth_parity, stage = 1, "Enclosed edge contours"
    indices = [
        index for index in indices
        if sum(1 for _ in _ancestors(index, parents)) % 2 == depth_parity
    ]
    counts[stage] = len(indices)

    filters = (
        ("Min area", settings.min_area, lambda i, limit: areas[i] >= limit),
        ("Max area", settings.max_area_percent, lambda i, limit: 100 * areas[i] <= limit * image_area),
        ("Aspect ratio", settings.max_aspect_ratio, lambda i, limit: _aspect_ratio(contours[i]) <= limit),
        ("Compactness", settings.min_compactness, lambda i, limit: _compactness(contours[i], areas[i]) >= limit),
        ("Solidity", settings.min_solidity, lambda i, limit: _solidity(contours[i], areas[i]) >= limit),
    )
    for name, limit, keep in filters:
        if limit is None:
            counts[f"{name} (off)"] = len(indices)
            continue
        indices = [index for index in indices if keep(index, limit)]
        counts[name] = len(indices)

    selected = set()
    for index in sorted(indices, key=lambda i: (-areas[i], i)):
        # Nested contours have filled overlap equal to the smaller area.
        # Only suppress near-coincident outlines in the same hierarchy branch.
        if any(
            ancestor in selected and areas[index] >= 0.90 * areas[ancestor]
            for ancestor in _ancestors(index, parents)
        ):
            continue
        selected.add(index)
    counts["After duplicate removal"] = len(selected)

    polygons = []
    for index in indices:
        if index in selected:
            contour = contours[index]
            epsilon = (settings.approximation_percent / 100) * cv2.arcLength(contour, True)
            polygon = cv2.approxPolyDP(contour, epsilon, True)
            if len(polygon) >= 3 and cv2.contourArea(polygon) > 0:
                polygons.append(polygon)
    counts["After polygon approximation"] = len(polygons)
    return polygons


def detect_buildings(image, method, settings=DetectionSettings(), road_barriers=None):
    if method not in DETECTION_METHODS:
        raise ValueError(f"Unknown detection method: {method}")
    if image is None or image.ndim != 3 or image.shape[2] != 3 or not image.size:
        raise ValueError("Expected a non-empty RGB image.")
    if image.dtype != np.uint8:
        raise ValueError("Expected 8-bit RGB pixels.")

    stages = {"Original": image}
    counts = {}
    mask = _candidate_mask(image, method, settings, stages)
    contours, parents = _find_contours(mask)
    counts["Raw mask contours"] = len(contours)

    opening = resolve_opening_kernel(method, settings.opening_kernel)
    for name, operation, size in (
        ("After opening", cv2.MORPH_OPEN, opening),
        ("After closing", cv2.MORPH_CLOSE, settings.closing_kernel),
    ):
        mask = _morphology(mask, operation, size)
        stages[name] = mask
        if size > 1:
            contours, parents = _find_contours(mask)
        detail = f"{size}×{size}" if size > 1 else "off"
        counts[f"{name} ({detail})"] = len(contours)

    polygons = _filter_contours(contours, parents, method, settings, mask.size, counts)
    zones = None
    if settings.road_zones:
        roads = road_barriers
        if roads is None:
            roads = draw_road_separators(image.shape[:2], settings.road_separators)
        if not np.any(roads):
            raise ValueError("Draw road separators before counting buildings by zone.")
        labels, zones = partition_zones(roads, settings.min_zone_area)
        polygons = assign_buildings(polygons, labels, zones)
        stages["Road barrier mask"] = roads
        stages[ZONES_STAGE] = draw_zones(image, roads, labels, zones)
        counts["Assigned to zones"] = len(polygons)
    overlay = image.copy()
    if polygons:
        cv2.drawContours(overlay, polygons, -1, (0, 255, 80), 2, cv2.LINE_AA)
    stages[FINAL_STAGE] = overlay
    return DetectionResult(polygons, stages, counts, zones)
