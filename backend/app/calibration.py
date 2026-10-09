"""Map between image pixels and real-world court metres.

With a fixed camera, four known points on the court (its outline corners) give
a homography between the image and the court's ground plane.

Important: the mapping is only valid for things touching the ground - player
feet and ball bounces. A ball in flight is above the plane, so projecting it
gives a wrong position; flight needs the trajectory fit (see docs/architecture.md).
"""

from __future__ import annotations

from collections.abc import Sequence

import cv2
import numpy as np

from .courts import CourtSpec, Point


class CourtCalibration:
    def __init__(self, court: CourtSpec, image_corners: Sequence[Point]):
        """image_corners: pixel positions of the court outline corners in the
        order far-left, far-right, near-right, near-left."""
        if len(image_corners) != 4:
            raise ValueError("Exactly four image corners are required")
        src = np.asarray(image_corners, dtype=np.float32)
        dst = np.asarray(court.corners, dtype=np.float32)
        if abs(cv2.contourArea(src)) < 1.0:
            raise ValueError("Image corners are collinear or coincide")
        self.court = court
        self.image_to_court_h = cv2.getPerspectiveTransform(src, dst)
        self.court_to_image_h = np.linalg.inv(self.image_to_court_h)

    @staticmethod
    def _apply(h: np.ndarray, points: Sequence[Point]) -> np.ndarray:
        pts = np.asarray(points, dtype=np.float64).reshape(-1, 1, 2)
        return cv2.perspectiveTransform(pts, h).reshape(-1, 2)

    def image_to_court(self, points: Sequence[Point]) -> np.ndarray:
        return self._apply(self.image_to_court_h, points)

    def court_to_image(self, points: Sequence[Point]) -> np.ndarray:
        return self._apply(self.court_to_image_h, points)

    def court_lines_in_image(self) -> list[list[list[float]]]:
        """Court markings as pixel segments, for drawing an overlay."""
        out = []
        for a, b in self.court.lines:
            pa, pb = self.court_to_image([a, b])
            out.append([pa.tolist(), pb.tolist()])
        return out
