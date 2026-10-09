# TennisTracker

Visual analysis of tennis from a single fixed phone camera behind the baseline:
track the ball and players, and report shot speed, angle and (eventually) spin.
Starts with saved clips, then live streams, then pickleball and padel.

## Status

| Piece | State |
| --- | --- |
| Court calibration from four clicked corners | Working |
| Court dimensions for tennis, pickleball, padel | Working |
| Ball tracking | Baseline (motion + colour), to be replaced by a learned detector |
| Speed and angle from hit and bounce positions | Maths in place, not yet wired to detected events |
| Web viewer with court overlay and ball trail | First version |
| Player tracking, hit/bounce detection, spin, live mode | Not started |

See [docs/architecture.md](docs/architecture.md) for how it fits together and
what one camera can realistically measure.

## Run it

Backend (Python 3.10+):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Frontend (Node 20+), in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, choose a clip, click the four court corners
(far-left, far-right, near-right, near-left), then press **Track ball**.

## Tests

```bash
cd backend && ruff check . && pytest
cd frontend && npm run build
```

## Roadmap

1. Hit and bounce detection from the ball track, wired into speed and angle.
2. Player detection and court positions.
3. Learned ball detector (TrackNet-style) for real footage.
4. 3D trajectory fit for speed along the path and a spin estimate.
5. Automatic court line detection.
6. Live streaming.
7. Pickleball and padel.
