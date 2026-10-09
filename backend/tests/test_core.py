import cv2
import numpy as np
import pytest

from app.calibration import CourtCalibration
from app.courts import COURTS
from app.pipeline import analyse_frames, analyse_video
from app.stats import GroundEvent, shot_stats

# A plausible behind-the-baseline view of a court in a 1920x1080 frame.
CORNERS = [(700, 300), (1220, 300), (1700, 1000), (220, 1000)]


def test_calibration_maps_corners_and_round_trips():
    court = COURTS["tennis"]
    cal = CourtCalibration(court, CORNERS)
    assert np.allclose(cal.image_to_court(CORNERS), court.corners, atol=1e-3)
    pts = [(960, 500), (400, 900)]
    assert np.allclose(cal.court_to_image(cal.image_to_court(pts)), pts, atol=1e-3)


def test_centre_of_net_is_on_the_image_centreline():
    cal = CourtCalibration(COURTS["tennis"], CORNERS)
    x, y = cal.court_to_image([(0.0, 0.0)])[0]
    assert x == pytest.approx(960, abs=0.5)
    assert 300 < y < 1000


def test_calibration_rejects_degenerate_corners():
    with pytest.raises(ValueError):
        CourtCalibration(COURTS["tennis"], [(0, 0), (1, 1), (2, 2), (3, 3)])


def test_shot_stats_speed_and_angle():
    # Baseline to the opposite service line, 18.285 m in 0.6 s, straight.
    s = shot_stats(GroundEvent(0.0, (0.0, -11.885)), GroundEvent(0.6, (0.0, 6.4)))
    assert s.speed_kmh == pytest.approx(109.71, abs=0.01)
    assert s.angle_deg == pytest.approx(0.0)
    cross = shot_stats(GroundEvent(0.0, (0.0, 0.0)), GroundEvent(1.0, (5.0, 5.0)))
    assert cross.angle_deg == pytest.approx(45.0)
    with pytest.raises(ValueError):
        shot_stats(GroundEvent(1.0, (0, 0)), GroundEvent(1.0, (1, 1)))


def _synthetic_frames(n=12):
    """A yellow ball moving across a dark green court."""
    for i in range(n):
        frame = np.full((360, 640, 3), (60, 90, 40), dtype=np.uint8)
        cv2.circle(frame, (50 + 40 * i, 100 + 10 * i), 5, (0, 255, 255), -1)
        yield frame


def test_ball_detector_follows_synthetic_ball():
    results = analyse_frames(_synthetic_frames(), fps=30.0)
    assert results[0].ball is None  # needs a previous frame for motion
    for i, r in enumerate(results[1:], start=1):
        assert r.ball is not None
        assert r.ball[0] == pytest.approx(50 + 40 * i, abs=2)
        assert r.ball[1] == pytest.approx(100 + 10 * i, abs=2)
    assert results[3].t == pytest.approx(0.1)


def test_analyse_video_reads_a_file(tmp_path):
    path = tmp_path / "clip.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 30.0, (640, 360))
    for frame in _synthetic_frames():
        writer.write(frame)
    writer.release()
    result = analyse_video(path)
    assert (result.width, result.height, len(result.frames)) == (640, 360, 12)
    assert sum(f.ball is not None for f in result.frames) >= 9
