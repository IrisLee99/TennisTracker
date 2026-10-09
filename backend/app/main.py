"""TennisTracker API."""

from __future__ import annotations

import tempfile
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .calibration import CourtCalibration
from .courts import COURTS
from .pipeline import analyse_video

app = FastAPI(title="TennisTracker")


class CalibrationRequest(BaseModel):
    sport: str = "tennis"
    # Pixel positions of the court corners: far-left, far-right, near-right, near-left.
    corners: list[tuple[float, float]] = Field(min_length=4, max_length=4)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/courts")
def courts() -> dict:
    return {name: {"length_m": c.length_m, "width_m": c.width_m} for name, c in COURTS.items()}


@app.post("/api/calibrate")
def calibrate(req: CalibrationRequest) -> dict:
    court = COURTS.get(req.sport)
    if court is None:
        raise HTTPException(404, f"Unknown sport: {req.sport}")
    try:
        calibration = CourtCalibration(court, req.corners)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {
        "sport": court.name,
        "image_to_court": calibration.image_to_court_h.tolist(),
        "court_lines": calibration.court_lines_in_image(),
    }


@app.post("/api/analyze")
def analyze(video: UploadFile) -> dict:
    suffix = Path(video.filename or "clip.mp4").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        while chunk := video.file.read(1 << 20):
            tmp.write(chunk)
        tmp.flush()
        try:
            result = analyse_video(tmp.name)
        except ValueError as exc:
            raise HTTPException(422, "Could not read that video file") from exc
    return asdict(result)
