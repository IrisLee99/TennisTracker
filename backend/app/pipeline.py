"""Run detectors over a video and produce a per-frame track."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .tracking.ball import BallDetector, MotionColourBallDetector


@dataclass(frozen=True)
class FrameResult:
    t: float
    ball: tuple[float, float] | None  # image pixels


@dataclass(frozen=True)
class VideoAnalysis:
    fps: float
    width: int
    height: int
    frames: list[FrameResult]


def analyse_frames(
    frames: Iterable[np.ndarray], fps: float, detector: BallDetector | None = None
) -> list[FrameResult]:
    detector = detector or MotionColourBallDetector()
    results = []
    for i, frame in enumerate(frames):
        d = detector.detect(frame)
        results.append(FrameResult(t=i / fps, ball=(d.x, d.y) if d else None))
    return results


def _read_frames(cap: cv2.VideoCapture) -> Iterable[np.ndarray]:
    while True:
        ok, frame = cap.read()
        if not ok:
            return
        yield frame


def analyse_video(path: str | Path, detector: BallDetector | None = None) -> VideoAnalysis:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {path}")
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frames = analyse_frames(_read_frames(cap), fps, detector)
    finally:
        cap.release()
    return VideoAnalysis(fps=fps, width=width, height=height, frames=frames)
