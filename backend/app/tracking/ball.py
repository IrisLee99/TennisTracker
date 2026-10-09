"""Ball detection.

`MotionColourBallDetector` is a classical baseline: a tennis ball is a small,
fast, yellow-green blob, so we keep pixels that are both ball-coloured and
moving. It needs no GPU or training data and is good enough to get the pipeline
running end to end, but it will be confused by other moving yellow things and
loses the ball against bright backgrounds. The plan is to swap in a learned
detector (TrackNet-style) behind the same `BallDetector` interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import cv2
import numpy as np


@dataclass(frozen=True)
class BallDetection:
    x: float
    y: float
    area: float


class BallDetector(Protocol):
    def detect(self, frame: np.ndarray) -> BallDetection | None:
        """Return the ball position in a BGR frame, or None if not seen."""


class MotionColourBallDetector:
    def __init__(
        self,
        hsv_low: tuple[int, int, int] = (20, 60, 120),
        hsv_high: tuple[int, int, int] = (45, 255, 255),
        motion_threshold: int = 18,
        min_area: int = 4,
        max_area: int = 600,
    ):
        self.hsv_low, self.hsv_high = hsv_low, hsv_high
        self.motion_threshold = motion_threshold
        self.min_area, self.max_area = min_area, max_area
        self._prev_gray: np.ndarray | None = None

    def detect(self, frame: np.ndarray) -> BallDetection | None:
        gray = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (5, 5), 0)
        prev, self._prev_gray = self._prev_gray, gray
        if prev is None:
            return None

        _, motion = cv2.threshold(
            cv2.absdiff(gray, prev), self.motion_threshold, 255, cv2.THRESH_BINARY
        )
        motion = cv2.dilate(motion, None, iterations=2)
        colour = cv2.inRange(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV), self.hsv_low, self.hsv_high)
        mask = cv2.bitwise_and(colour, motion)

        count, _, stats, centroids = cv2.connectedComponentsWithStats(mask)
        best: BallDetection | None = None
        for i in range(1, count):
            area = float(stats[i, cv2.CC_STAT_AREA])
            w, h = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
            if not self.min_area <= area <= self.max_area:
                continue
            if max(w, h) > 4 * min(w, h):  # long streaks are not the ball
                continue
            if best is None or area > best.area:
                best = BallDetection(float(centroids[i][0]), float(centroids[i][1]), area)
        return best
