"""Controls and diagnostic views for building detection."""

from colorsys import hsv_to_rgb
from dataclasses import replace
import tkinter as tk
from tkinter import ttk

from edge_detector.buildings import (
    FINAL_STAGE,
    HSV_OVERLAY_STAGE,
    HSV_SEGMENTATION,
    ZONES_STAGE,
    DetectionSettings,
    resolve_opening_kernel,
    validate_hsv_range,
)
from edge_detector.detection_config import GEOMETRIC_FILTERS


def _format_range(bounds):
    low, high = bounds
    return f"{' '.join(map(str, low))} : {' '.join(map(str, high))}"


def _parse_range(line):
    try:
        low, high = (tuple(map(int, part.split())) for part in line.split(":"))
    except ValueError as exc:
        raise ValueError("Enter HSV bounds as H S V : H S V, one range per line.") from exc
    validate_hsv_range(low, high)
    return low, high


def _number(value, label, minimum, maximum, parse=float):
    try:
        number = parse(value.get())
    except ValueError as exc:
        raise ValueError(f"{label} must be a number.") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"{label} must be between {minimum:g} and {maximum:g}.")
    return number


class DetectionControls(ttk.Frame):
    def __init__(self, parent, edit_roads):
        super().__init__(parent)
        defaults = DetectionSettings()
        self._base_settings = defaults
        self.columnconfigure(0, weight=1)

        self.hsv_frame = ttk.LabelFrame(self, text="HSV exclusions")
        self.hsv_frame.grid(row=1, column=0, sticky="ew", pady=3)
        self.hsv_frame.columnconfigure(0, weight=1)
        ttk.Label(
            self.hsv_frame, text="H S V : H S V per line · H 0–179, S/V 0–255\n"
                                 "Color preview uses midpoint saturation and brightness."
        ).grid(row=0, column=0, sticky="w", padx=6)
        self.hsv_ranges = tk.Text(self.hsv_frame, height=2, width=35, wrap="none")
        self.hsv_ranges.grid(row=1, column=0, sticky="ew", padx=(6, 0))
        scroll = ttk.Scrollbar(self.hsv_frame, command=self.hsv_ranges.yview)
        scroll.grid(row=1, column=1, sticky="ns", padx=(0, 6))
        self.swatches = tk.Canvas(self.hsv_frame, width=104, height=1, highlightthickness=0)
        self.swatches.grid(row=1, column=2, sticky="ns", padx=(0, 6))

        def hsv_scrolled(first, last):
            scroll.set(first, last)
            self._draw_range_previews()

        self.hsv_ranges.configure(yscrollcommand=hsv_scrolled)
        self.hsv_ranges.insert("1.0", "\n".join(map(_format_range, defaults.hsv_ranges)))
        self.hsv_ranges.edit_modified(False)
        self.hsv_ranges.bind("<<Modified>>", self._hsv_modified)
        self.hsv_ranges.bind("<Configure>", self._draw_range_previews)
        asphalt_row = ttk.Frame(self.hsv_frame)
        asphalt_row.grid(row=2, column=0, columnspan=2, sticky="w", padx=6, pady=3)
        self.exclude_asphalt = tk.BooleanVar(self, defaults.exclude_asphalt)
        self.asphalt_range = tk.StringVar(self, _format_range(defaults.asphalt_range))
        self._optional_entry(
            asphalt_row, 0, 0, "Exclude asphalt", self.exclude_asphalt, self.asphalt_range, 25
        )
        self.asphalt_swatch = tk.Canvas(asphalt_row, width=104, height=16, highlightthickness=0)
        self.asphalt_swatch.grid(row=0, column=2)
        self.asphalt_range.trace_add("write", self._draw_asphalt_preview)
        self.exclude_asphalt.trace_add("write", self._draw_asphalt_preview)
        self.roof_frame = ttk.LabelFrame(self, text="HSV roof colors")
        self.roof_frame.grid(row=5, column=0, sticky="ew", pady=3)
        self.roof_frame.columnconfigure(0, weight=1)
        ttk.Label(
            self.roof_frame, text="Separate ranges with ;  ·  Empty keeps all non-excluded colors."
        ).grid(row=0, column=0, sticky="w", padx=6)
        self.roof_ranges = tk.StringVar(self, "; ".join(map(_format_range, defaults.roof_hsv_ranges)))
        ttk.Entry(self.roof_frame, textvariable=self.roof_ranges).grid(
            row=1, column=0, sticky="ew", padx=6, pady=(0, 4)
        )

        morphology = ttk.LabelFrame(self, text="Morphology · odd kernels, 1 disables")
        morphology.grid(row=3, column=0, sticky="ew", pady=3)
        self.opening = self._entry(morphology, 0, 0, "Opening", "auto")
        self.closing = self._entry(morphology, 0, 2, "Closing", defaults.closing_kernel)
        self.morphology_hint = ttk.Label(morphology, wraplength=450)
        self.morphology_hint.grid(row=1, column=0, columnspan=4, sticky="w", padx=6)
        self.opening.trace_add("write", self._update_morphology_hint)
        self.closing.trace_add("write", self._update_morphology_hint)

        geometry = ttk.LabelFrame(self, text="Contour filtering")
        geometry.grid(row=4, column=0, sticky="ew", pady=3)
        self.filters = {}
        for index, (key, label, _, _, fallback) in enumerate(GEOMETRIC_FILTERS):
            default = getattr(defaults, key)
            enabled = tk.BooleanVar(self, default is not None)
            value = tk.StringVar(self, f"{default if default is not None else fallback:g}")
            self._optional_entry(geometry, index // 2, 2 * (index % 2), label, enabled, value)
            self.filters[key] = (enabled, value)
        self.approximation = self._entry(
            geometry, 3, 0, "Approx. (% of perimeter)", defaults.approximation_percent
        )

        roads = ttk.LabelFrame(self, text="Road zones")
        roads.grid(row=6, column=0, sticky="ew", pady=3)
        self.road_zones = tk.BooleanVar(self, defaults.road_zones)
        self.road_separators = defaults.road_separators
        ttk.Checkbutton(roads, text="Count separately by road zone", variable=self.road_zones).pack(anchor="w")
        road_settings = ttk.Frame(roads)
        road_settings.columnconfigure(1, weight=1)
        self.min_zone_area = self._entry(road_settings, 0, 0, "Min zone area (px²)", defaults.min_zone_area)
        ttk.Button(road_settings, text="Draw road separators", command=edit_roads).grid(
            row=0, column=2, columnspan=2, sticky="w", padx=6
        )

        def update_roads(*_):
            if self.road_zones.get():
                road_settings.pack(fill="x")
            else:
                road_settings.pack_forget()

        self.road_zones.trace_add("write", update_roads)
        update_roads()
        self._update_morphology_hint()

    def _update_morphology_hint(self, *_):
        auto = self.opening.get().strip().lower() == "auto"
        try:
            opening = resolve_opening_kernel(
                HSV_SEGMENTATION, None if auto else _number(self.opening, "Opening", 1, 101, int)
            )
            closing = _number(self.closing, "Closing", 1, 101, int)
            if opening % 2 == 0 or closing % 2 == 0:
                raise ValueError
        except ValueError:
            self.morphology_hint.configure(text="Use odd kernel sizes from 1 to 101, or auto for Opening.")
            return

        opening_text = f"{opening}×{opening}" if opening > 1 else "off"
        closing_text = f"{closing}×{closing}" if closing > 1 else "off"
        suffix = " (auto)" if auto else ""
        self.morphology_hint.configure(
            text=f"Opening {opening_text}{suffix} · Closing {closing_text}"
        )

    @staticmethod
    def _draw_swatch(canvas, line, y, height):
        try:
            low, high = _parse_range(line)
        except ValueError:
            canvas.create_text(3, y + height / 2, anchor="w", text="Invalid range")
            return
        saturation = (low[1] + high[1]) / 510
        brightness = (low[2] + high[2]) / 510
        for index in range(26):
            hue = (low[0] + (high[0] - low[0]) * index / 25) / 180
            rgb = tuple(round(value * 255) for value in hsv_to_rgb(hue, saturation, brightness))
            canvas.create_rectangle(index * 4, y, (index + 1) * 4, y + height,
                                    fill="#%02x%02x%02x" % rgb, width=0)

    def _hsv_modified(self, _):
        if self.hsv_ranges.edit_modified():
            self.hsv_ranges.edit_modified(False)
            self._draw_range_previews()

    def _draw_range_previews(self, *_):
        self.swatches.delete("all")
        first = int(self.hsv_ranges.index("@0,0").split(".")[0])
        last = int(self.hsv_ranges.index("end-1c").split(".")[0])
        for row in range(first, last + 1):
            index = f"{row}.0"
            bounds = self.hsv_ranges.dlineinfo(index)
            if bounds is None:
                break
            line = self.hsv_ranges.get(index, f"{index} lineend")
            if line.strip():
                self._draw_swatch(self.swatches, line, bounds[1] + 2, max(1, bounds[3] - 4))

    def _draw_asphalt_preview(self, *_):
        self.asphalt_swatch.delete("all")
        if self.exclude_asphalt.get():
            self._draw_swatch(self.asphalt_swatch, self.asphalt_range.get(), 0, 16)

    @staticmethod
    def _entry(parent, row, column, label, default):
        value = tk.StringVar(parent, str(default))
        ttk.Label(parent, text=label).grid(row=row, column=column, padx=6, pady=3, sticky="w")
        ttk.Entry(parent, textvariable=value, width=7).grid(
            row=row, column=column + 1, padx=(0, 8), pady=3, sticky="w"
        )
        return value

    @staticmethod
    def _optional_entry(parent, row, column, label, enabled, value, width=7):
        ttk.Checkbutton(parent, text=label, variable=enabled).grid(
            row=row, column=column, padx=4, pady=2, sticky="w"
        )
        entry = ttk.Entry(parent, textvariable=value, width=width)
        entry.grid(row=row, column=column + 1, padx=(0, 8), pady=2, sticky="w")

        def update_state(*_):
            entry.configure(state="normal" if enabled.get() else "disabled")

        enabled.trace_add("write", update_state)
        update_state()

    def settings(self, include_inactive=False):
        settings = {
            "opening_kernel": None,
            "closing_kernel": _number(self.closing, "Closing kernel", 1, 101, int),
            "approximation_percent": _number(self.approximation, "Approximation", 0, 10),
            "road_zones": self.road_zones.get(),
        }
        if include_inactive or settings["road_zones"]:
            settings.update(
                min_zone_area=_number(self.min_zone_area, "Min zone area", 1, 1e12, int),
                road_separators=self.road_separators,
            )
        if self.opening.get().strip().lower() != "auto":
            settings["opening_kernel"] = _number(self.opening, "Opening kernel", 1, 101, int)
        lines = self.hsv_ranges.get("1.0", "end-1c").splitlines()
        settings["hsv_ranges"] = tuple(_parse_range(line) for line in lines if line.strip())
        settings["exclude_asphalt"] = self.exclude_asphalt.get()
        if include_inactive or settings["exclude_asphalt"]:
            settings["asphalt_range"] = _parse_range(self.asphalt_range.get())
        settings["roof_hsv_ranges"] = tuple(
            _parse_range(part) for part in self.roof_ranges.get().split(";") if part.strip()
        )

        for key, label, minimum, maximum, _ in GEOMETRIC_FILTERS:
            enabled, value = self.filters[key]
            settings[key] = _number(value, label, minimum, maximum) if enabled.get() else None
        return replace(self._base_settings, **settings)

    def apply_settings(self, settings):
        self._base_settings = settings
        self.hsv_ranges.delete("1.0", "end")
        self.hsv_ranges.insert("1.0", "\n".join(map(_format_range, settings.hsv_ranges)))
        self.asphalt_range.set(_format_range(settings.asphalt_range))
        self.roof_ranges.set("; ".join(map(_format_range, settings.roof_hsv_ranges)))
        self.exclude_asphalt.set(settings.exclude_asphalt)
        self.opening.set("auto" if settings.opening_kernel is None else str(settings.opening_kernel))
        self.closing.set(str(settings.closing_kernel))
        self.approximation.set(str(settings.approximation_percent))
        self.min_zone_area.set(str(settings.min_zone_area))
        self.road_separators = settings.road_separators
        self.road_zones.set(settings.road_zones)
        for key, _, _, _, fallback in GEOMETRIC_FILTERS:
            enabled, value = self.filters[key]
            threshold = getattr(settings, key)
            value.set(str(fallback if threshold is None else threshold))
            enabled.set(threshold is not None)


def show_detection_result(parent, method, result, photo_factory):
    window = tk.Toplevel(parent)
    window.title(f"{method} | Building detection")
    window.columnconfigure(0, weight=1)
    window.rowconfigure(1, weight=1)

    controls = ttk.Frame(window)
    controls.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
    ttk.Label(controls, text=f"Detected buildings (estimate) · {result.count}").pack(
        side="left", padx=(0, 12)
    )
    stage = tk.StringVar(window, ZONES_STAGE if result.zones is not None else FINAL_STAGE)
    ttk.Combobox(
        controls, textvariable=stage, values=tuple(result.stages), state="readonly", width=26
    ).pack(side="left")
    ttk.Button(controls, text="Close", command=window.destroy).pack(side="right")

    preview = ttk.Label(window)
    preview.grid(row=1, column=0, padx=8, pady=(0, 8))
    legend = ttk.Label(window, text="Pink highlights pixels excluded by the HSV mask.")
    legend.grid(row=2, column=0, padx=8, pady=(0, 8))
    counts = ttk.LabelFrame(window, text="Contours by stage")
    counts.grid(row=1, column=1, sticky="n", padx=(0, 8), pady=(0, 8))
    for row, (name, count) in enumerate(result.counts.items()):
        ttk.Label(counts, text=name).grid(row=row, column=0, sticky="w", padx=6, pady=2)
        ttk.Label(counts, text=str(count)).grid(row=row, column=1, sticky="e", padx=6, pady=2)
    if result.zones is not None:
        table = ttk.Treeview(counts, columns=("area", "buildings"), height=5, show="tree headings")
        table.heading("#0", text="Zone")
        table.heading("area", text="Area (px²)")
        table.heading("buildings", text="Buildings")
        for column in ("#0", "area", "buildings"):
            table.column(column, width=70, anchor="center")
        for zone in result.zones:
            table.insert("", "end", text=str(zone.number), values=(zone.area, zone.buildings))
        table.grid(row=len(result.counts), column=0, columnspan=2, sticky="ew", padx=4, pady=4)
        scroll = ttk.Scrollbar(counts, command=table.yview)
        scroll.grid(row=len(result.counts), column=2, sticky="ns")
        table.configure(yscrollcommand=scroll.set)

    max_size = (
        min(1000, int(window.winfo_screenwidth() * 0.66)),
        min(800, int(window.winfo_screenheight() * 0.75)),
    )

    def update_preview(*_):
        photo = photo_factory(result.stages[stage.get()], max_size)
        preview.configure(image=photo)
        preview.image = photo
        if stage.get() == HSV_OVERLAY_STAGE:
            legend.configure(text="Pink highlights pixels excluded by the HSV mask.")
            legend.grid()
        elif stage.get() == ZONES_STAGE:
            legend.configure(text="Orange marks road barriers. Each zone label shows its number and count.")
            legend.grid()
        else:
            legend.grid_remove()

    stage.trace_add("write", update_preview)
    update_preview()
    return window
