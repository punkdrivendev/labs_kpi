"""JSON configuration for Object Detection."""

from dataclasses import asdict, fields
import json
from pathlib import Path

from edge_detector.buildings import DETECTION_METHODS, DetectionSettings, validate_hsv_range


GEOMETRIC_FILTERS = (
    ("min_area", "Min area (px²)", 0, 1e12, 40),
    ("max_area_percent", "Max area (% of image)", 0, 100, 10),
    ("max_aspect_ratio", "Max aspect ratio", 1, 1000, 8),
    ("min_compactness", "Min compactness (0–1)", 0, 1, 0.08),
    ("min_solidity", "Min solidity (0–1)", 0, 1, 0.5),
)


def validate_config(method, options):
    if method not in DETECTION_METHODS:
        raise ValueError("Unknown detection method.")
    if isinstance(options, dict):
        defaults = asdict(DetectionSettings())
        added = ("roof_hsv_ranges", "road_zones", "min_zone_area", "road_separators")
        options = {**{key: defaults[key] for key in added}, **options}
        # Older presets may still contain automatic road detection settings.
        for key in ("road_hsv_ranges", "road_opening_kernel", "road_closing_kernel"):
            options.pop(key, None)
    if not isinstance(options, dict) or options.keys() != {field.name for field in fields(DetectionSettings)}:
        raise ValueError("The settings object must contain all detection parameters.")

    def number(value, name, low, high, integer=False):
        types = (int,) if integer else (int, float)
        if type(value) not in types or not low <= value <= high:
            raise ValueError(f"{name} must be {'an integer' if integer else 'a number'} between {low:g} and {high:g}.")

    def sequence(value, name, length=None):
        if not isinstance(value, (list, tuple)) or (length is not None and len(value) != length):
            raise ValueError(f"Invalid array for {name}.")
        return tuple(value)

    def hsv(bounds):
        low, high = sequence(bounds, "HSV range", 2)
        low, high = sequence(low, "lower HSV bound", 3), sequence(high, "upper HSV bound", 3)
        if any(type(value) is not int for value in (*low, *high)):
            raise ValueError("HSV bounds must be integers.")
        validate_hsv_range(low, high)
        return low, high

    def separator(line):
        points = tuple(sequence(point, "road separator point", 2)
                       for point in sequence(line, "road separator"))
        if len(points) < 2:
            raise ValueError("Each road separator needs at least two points.")
        for x, y in points:
            number(x, "Road separator x", 0, 1)
            number(y, "Road separator y", 0, 1)
        return points

    brightness, contrast, blur = sequence(options["preprocessing"], "preprocessing", 3)
    number(brightness, "Brightness", -255, 255, True)
    number(contrast, "Contrast", 0.1, 3)
    if abs(contrast * 10 - round(contrast * 10)) > 1e-8:
        raise ValueError("Contrast must use steps of 0.1.")
    number(blur, "Gaussian kernel", 1, 21, True)
    if blur % 2 == 0:
        raise ValueError("Gaussian kernel must be odd.")
    low, high = sequence(options["canny_thresholds"], "Canny thresholds", 2)
    number(low, "Low Canny threshold", 0, 2047, True)
    number(high, "High Canny threshold", low + 1, 2048, True)
    number(options["hsv_boundary_margin"], "HSV boundary margin", 0, 20, True)
    number(options["approximation_percent"], "Approximation", 0, 10)
    for key in ("exclude_asphalt", "road_zones"):
        if type(options[key]) is not bool:
            raise ValueError(f"{key} must be true or false.")
    number(options["min_zone_area"], "Minimum zone area", 1, 1e12, True)
    for key in ("opening_kernel", "closing_kernel"):
        value = options[key]
        if key == "opening_kernel" and value is None:
            continue
        number(value, key, 1, 101, True)
        if value % 2 == 0:
            raise ValueError(f"{key} must be odd.")
    for key, label, minimum, maximum, _ in GEOMETRIC_FILTERS:
        if options[key] is not None:
            number(options[key], label, minimum, maximum)
    normalized = dict(options)
    normalized.update(
        preprocessing=(brightness, contrast, blur),
        canny_thresholds=(low, high),
        hsv_ranges=tuple(hsv(bounds) for bounds in sequence(options["hsv_ranges"], "HSV ranges")),
        roof_hsv_ranges=tuple(
            hsv(bounds) for bounds in sequence(options["roof_hsv_ranges"], "HSV roof ranges")
        ),
        asphalt_range=hsv(options["asphalt_range"]),
        road_separators=tuple(separator(line) for line in sequence(options["road_separators"], "Road separators")),
    )
    return DetectionSettings(**normalized)


def load_config(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.keys() != {"method", "settings"}:
        raise ValueError("Expected a JSON object with method and settings.")
    return data["method"], validate_config(data["method"], data["settings"])


def save_config(path, method, settings):
    options = asdict(settings)
    validate_config(method, options)
    data = {"method": method, "settings": options}
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
