"""Three trackers initialized on the same rectangle in the first frame."""

import cv2
import numpy as np


def clip_box(box, shape):
    x, y, width, height = box
    rows, cols = shape[:2]
    left, top = max(0, x), max(0, y)
    right, bottom = min(cols, x + width), min(rows, y + height)
    return left, top, max(0, right - left), max(0, bottom - top)


def _crop(image, box):
    x, y, width, height = box
    return image[y:y + height, x:x + width]


def _gray(frame):
    return cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (3, 3), 0)


class TemplateTracker:
    name = "Template matching"

    def __init__(self, frame, box):
        self.template = _crop(_gray(frame), box).copy()
        self.has_texture = self.template.std() >= 1

    def update(self, frame):
        image = _gray(frame)
        height, width = self.template.shape
        if not self.has_texture or height > image.shape[0] or width > image.shape[1]:
            return None
        response = cv2.matchTemplate(image, self.template, cv2.TM_CCOEFF_NORMED)
        _, score, _, (x, y) = cv2.minMaxLoc(response)
        if score < 0.55:
            return None
        return x, y, width, height


class CamShiftTracker:
    name = "CamShift"

    def __init__(self, frame, box):
        self.box = box
        hsv = _crop(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV), box)
        self.histogram = cv2.calcHist([hsv], [0, 1], self._color_mask(hsv), [24, 16], [0, 180, 0, 256])
        cv2.normalize(self.histogram, self.histogram, 0, 255, cv2.NORM_MINMAX)
        self.criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)

    @staticmethod
    def _color_mask(hsv):
        return cv2.inRange(hsv, (0, 32, 24), (179, 255, 255))

    def update(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        response = cv2.calcBackProject([hsv], [0, 1], self.histogram, [0, 180, 0, 256], 1)
        response = cv2.bitwise_and(response, self._color_mask(hsv))
        if not np.any(_crop(response, self.box)):
            return None
        _, box = cv2.CamShift(response, self.box, self.criteria)
        box = clip_box(box, frame.shape)
        if min(box[2:]) < 4 or _crop(response, box).mean() < 6:
            return None
        self.box = box
        return box


class LucasKanadeTracker:
    name = "Lucas–Kanade"

    def __init__(self, frame, box):
        self.previous = _gray(frame)
        self.box = np.array(box, dtype=np.float32)
        self.points = self._find_points(self.previous, box)

    @staticmethod
    def _find_points(gray, box):
        x, y, width, height = box
        margin_x, margin_y = width // 12, height // 12
        mask = np.zeros(gray.shape, dtype=np.uint8)
        mask[y + margin_y:y + height - margin_y, x + margin_x:x + width - margin_x] = 255
        return cv2.goodFeaturesToTrack(gray, 80, 0.01, 4, mask=mask)

    def update(self, frame):
        if self.points is None or len(self.points) < 4:
            return None
        gray = _gray(frame)
        options = {"winSize": (21, 21), "maxLevel": 3}
        new, forward, _ = cv2.calcOpticalFlowPyrLK(self.previous, gray, self.points, None, **options)
        if new is None:
            return None
        valid = forward.ravel() == 1
        old_points = self.points[valid]
        new_points = new[valid]
        if len(new_points) < 4:
            return None
        returned, backward, _ = cv2.calcOpticalFlowPyrLK(gray, self.previous, new_points, None, **options)
        if returned is None:
            return None
        reliable = (backward.ravel() == 1) & (np.linalg.norm(returned - old_points, axis=2).ravel() < 2)
        old_points, new_points = old_points[reliable], new_points[reliable]
        if len(new_points) < 4:
            return None
        transform, inliers = cv2.estimateAffinePartial2D(
            old_points, new_points, method=cv2.RANSAC, ransacReprojThreshold=2.0
        )
        if transform is None or inliers is None:
            return None
        consistent = inliers.ravel() != 0
        if consistent.sum() < max(4, 0.6 * len(new_points)):
            return None
        scale = np.linalg.norm(transform[:, 0])
        if not 0.7 <= scale <= 1.4:
            return None
        center = self.box[:2] + self.box[2:] / 2
        center = transform[:, :2] @ center + transform[:, 2]
        size = self.box[2:] * scale
        next_box = np.concatenate((center - size / 2, size))
        box = clip_box(tuple(np.rint(next_box).astype(int)), gray.shape)
        if min(box[2:]) < 4:
            return None
        self.box = next_box
        self.previous = gray
        self.points = new_points[consistent]
        return box


TRACKERS = (TemplateTracker, CamShiftTracker, LucasKanadeTracker)
