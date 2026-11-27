"""Split a map along a road mask and assign building contours to zones."""

from dataclasses import dataclass
from itertools import cycle

import cv2
import numpy as np


@dataclass
class Zone:
    number: int
    area: int
    buildings: int = 0


def draw_road_separators(shape, lines):
    height, width = shape
    mask = np.zeros(shape, dtype=np.uint8)
    for line in lines:
        points = np.array(
            [(round(x * (width - 1)), round(y * (height - 1))) for x, y in line],
            dtype=np.int32,
        )
        cv2.polylines(mask, [points], False, 255, 9)
    return mask


def partition_zones(roads, min_area):
    free = cv2.bitwise_not(roads)
    _, components, stats, _ = cv2.connectedComponentsWithStats(free, connectivity=4)
    labels = np.zeros(roads.shape, dtype=np.int32)
    zones = []
    outline_mask = np.zeros_like(roads)
    ordered = sorted(range(1, len(stats)), key=lambda i: -stats[i, cv2.CC_STAT_AREA])
    for component in ordered:
        x, y, width, height, area = map(int, stats[component])
        if area < min_area:
            break
        region = np.s_[y:y+height, x:x+width]
        pixels = components[region] == component
        # A retained outer zone has already claimed any enclosed components.
        if np.any(labels[region][pixels]):
            continue
        contours, _ = cv2.findContours(pixels.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        outline_mask[region] = 0
        cv2.drawContours(outline_mask[region], contours, -1, 255, cv2.FILLED)
        select = (outline_mask[region] != 0) & (roads[region] == 0) & (labels[region] == 0)
        number = len(zones) + 1
        labels[region][select] = number
        zones.append(Zone(number, int(np.count_nonzero(select))))
    return labels, zones


def assign_buildings(polygons, labels, zones):
    retained = []
    for polygon in polygons:
        x, y, width, height = cv2.boundingRect(polygon)
        mask = np.zeros((height, width), dtype=np.uint8)
        local_polygon = polygon - np.array([x, y], dtype=np.int32)
        cv2.fillPoly(mask, [local_polygon], 255)
        overlap = labels[y:y+height, x:x+width][mask != 0]
        counts = np.bincount(overlap, minlength=len(zones) + 1)
        if not zones:
            continue
        index = int(np.argmax(counts[1:]))
        if 2 * counts[index + 1] <= overlap.size:
            continue
        zones[index].buildings += 1
        retained.append(polygon)
    return retained


def draw_zones(image, roads, labels, zones):
    overlay = image.copy()
    overlay[roads != 0] = (255, 90, 30)
    colors = cycle(((60, 200, 255), (255, 212, 70), (160, 112, 255),
                    (80, 240, 130), (250, 110, 200), (70, 240, 225)))
    palette = np.zeros((len(zones) + 1, 3), dtype=np.uint8)
    for zone, color in zip(zones, colors):
        palette[zone.number] = color
    selected = labels > 0
    overlay[selected] = (0.65 * image[selected] + 0.35 * palette[labels[selected]]).astype(np.uint8)
    for zone in zones:
        pixels = (labels == zone.number).astype(np.uint8)
        distance = cv2.distanceTransform(pixels, cv2.DIST_L2, 3)
        _, _, _, (x, y) = cv2.minMaxLoc(distance)
        text = f"{zone.number}: {zone.buildings}"
        cv2.putText(overlay, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(overlay, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 1, cv2.LINE_AA)
    return overlay
