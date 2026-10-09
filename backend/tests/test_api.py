import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.courts import COURTS
from app.main import app

CORNERS = [(700, 300), (1220, 300), (1700, 1000), (220, 1000)]
client = TestClient(app)


def test_api_calibrate_and_errors():
    assert client.get("/api/health").json() == {"status": "ok"}
    assert set(client.get("/api/courts").json()) == {"tennis", "pickleball", "padel"}
    res = client.post("/api/calibrate", json={"sport": "tennis", "corners": CORNERS})
    assert res.status_code == 200
    assert len(res.json()["court_lines"]) == len(COURTS["tennis"].lines)
    assert (
        client.post("/api/calibrate", json={"sport": "golf", "corners": CORNERS}).status_code == 404
    )
    bad = client.post("/api/analyze", files={"video": ("x.mp4", b"not a video", "video/mp4")})
    assert bad.status_code == 422


def test_api_analyze_upload(tmp_path):
    path = tmp_path / "clip.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 30.0, (640, 360))
    for i in range(12):
        frame = np.full((360, 640, 3), (60, 90, 40), dtype=np.uint8)
        cv2.circle(frame, (50 + 40 * i, 100 + 10 * i), 5, (0, 255, 255), -1)
        writer.write(frame)
    writer.release()
    with path.open("rb") as fh:
        res = client.post("/api/analyze", files={"video": ("clip.avi", fh, "video/avi")})
    assert res.status_code == 200
    assert len(res.json()["frames"]) == 12
