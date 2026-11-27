"""Measure and export the results of tracking a shared video sequence."""

import csv
from dataclasses import astuple, dataclass
from time import perf_counter

from video_tracking.trackers import TRACKERS


def box_iou(first, second):
    if first is None:
        return 0.0
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    width = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    height = max(0, min(ay + ah, by + bh) - max(ay, by))
    intersection = width * height
    return intersection / (aw * ah + bw * bh - intersection)


def load_reference_boxes(path):
    fields = ("frame", "x", "y", "width", "height")
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(fields):
            raise ValueError("Expected CSV header: frame,x,y,width,height")
        boxes = {}
        for row in reader:
            try:
                frame, x, y, width, height = (int(row[field]) for field in fields)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Expected integer coordinates on line {reader.line_num}.") from exc
            if min(frame, x, y) < 0 or min(width, height) <= 0 or frame in boxes:
                raise ValueError(f"Invalid box or duplicate frame on line {reader.line_num}.")
            boxes[frame] = (x, y, width, height)
        if not boxes:
            raise ValueError("The reference CSV has no boxes.")
    return boxes


@dataclass
class Measurement:
    frame: int
    method: str
    tracked: bool
    x: int | None
    y: int | None
    width: int | None
    height: int | None
    update_ms: float
    iou: float | None


@dataclass
class TrackingSummary:
    frames: int = 0
    tracked: int = 0
    update_ms: float = 0.0
    reference_frames: int = 0
    iou_sum: float = 0.0

    def add(self, measurement):
        self.frames += 1
        self.tracked += int(measurement.tracked)
        self.update_ms += measurement.update_ms
        if measurement.iou is not None:
            self.reference_frames += 1
            self.iou_sum += measurement.iou


class TrackingExperiment:
    def __init__(self, first_frame, box, reference):
        self.trackers = [tracker(first_frame, box) for tracker in TRACKERS]
        self.reference = reference
        self.measurements = []
        self.summary = {tracker.name: TrackingSummary() for tracker in self.trackers}

    def update(self, frame_number, frame):
        expected = self.reference.get(frame_number)
        detections = []
        for tracker in self.trackers:
            start = perf_counter()
            box = tracker.update(frame)
            elapsed = (perf_counter() - start) * 1000
            coordinates = box if box is not None else (None, None, None, None)
            measurement = Measurement(
                frame_number, tracker.name, box is not None, *coordinates,
                elapsed, box_iou(box, expected) if expected is not None else None,
            )
            self.measurements.append(measurement)
            self.summary[tracker.name].add(measurement)
            detections.append(box)
        return detections

    def export_csv(self, path, source):
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(("source", *Measurement.__dataclass_fields__))
            writer.writerows((source, *astuple(item)) for item in self.measurements)
