import { useEffect, useMemo, useRef, useState, type MouseEvent } from "react";
import { analyze, calibrate, type Calibration, type Point, type VideoAnalysis } from "./api";

const CORNER_NAMES = ["far-left", "far-right", "near-right", "near-left"];
const TRAIL_SECONDS = 0.6;

export default function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [sport, setSport] = useState("tennis");
  const [corners, setCorners] = useState<Point[]>([]);
  const [calibration, setCalibration] = useState<Calibration | null>(null);
  const [analysis, setAnalysis] = useState<VideoAnalysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const videoUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);
  useEffect(() => () => void (videoUrl && URL.revokeObjectURL(videoUrl)), [videoUrl]);

  // Recalibrate whenever four corners are set or the sport changes.
  useEffect(() => {
    setCalibration(null);
    if (corners.length !== 4) return;
    let stale = false;
    calibrate(sport, corners)
      .then((c) => !stale && setCalibration(c))
      .catch((e: Error) => !stale && setError(e.message));
    return () => {
      stale = true;
    };
  }, [corners, sport]);

  // Redraw the overlay on every animation frame so it follows playback.
  useEffect(() => {
    let raf = 0;
    const draw = () => {
      raf = requestAnimationFrame(draw);
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext("2d");
      if (!video || !canvas || !ctx || !video.videoWidth) return;
      if (canvas.width !== video.videoWidth) canvas.width = video.videoWidth;
      if (canvas.height !== video.videoHeight) canvas.height = video.videoHeight;
      const unit = canvas.width / 400; // keeps strokes visible at any resolution
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (calibration) {
        ctx.strokeStyle = "rgba(0, 220, 255, 0.9)";
        ctx.lineWidth = unit;
        for (const [a, b] of calibration.court_lines) {
          ctx.beginPath();
          ctx.moveTo(a[0], a[1]);
          ctx.lineTo(b[0], b[1]);
          ctx.stroke();
        }
      }

      ctx.fillStyle = "#ff3d71";
      for (const [x, y] of corners) {
        ctx.beginPath();
        ctx.arc(x, y, unit * 2.5, 0, Math.PI * 2);
        ctx.fill();
      }

      if (analysis) {
        const t = video.currentTime;
        const trail = analysis.frames.filter((f) => f.ball && f.t <= t && f.t > t - TRAIL_SECONDS);
        trail.forEach((f, i) => {
          const [x, y] = f.ball as Point;
          ctx.fillStyle = `rgba(255, 235, 59, ${(i + 1) / trail.length})`;
          ctx.beginPath();
          ctx.arc(x, y, unit * 2, 0, Math.PI * 2);
          ctx.fill();
        });
      }
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [calibration, corners, analysis]);

  function onPick(e: MouseEvent<HTMLDivElement>) {
    const video = videoRef.current;
    if (!video || !video.videoWidth || corners.length >= 4) return;
    const rect = video.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * video.videoWidth;
    const y = ((e.clientY - rect.top) / rect.height) * video.videoHeight;
    setError(null);
    setCorners([...corners, [x, y]]);
  }

  async function runAnalysis() {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      setAnalysis(await analyze(file));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const detected = analysis?.frames.filter((f) => f.ball).length ?? 0;

  return (
    <main>
      <h1>TennisTracker</h1>
      <div className="controls">
        <input
          type="file"
          accept="video/*"
          onChange={(e) => {
            setFile(e.target.files?.[0] ?? null);
            setCorners([]);
            setAnalysis(null);
            setError(null);
          }}
        />
        <select value={sport} onChange={(e) => setSport(e.target.value)}>
          <option value="tennis">Tennis</option>
          <option value="pickleball">Pickleball</option>
          <option value="padel">Padel</option>
        </select>
        <button onClick={() => setCorners([])} disabled={!corners.length}>
          Reset corners
        </button>
        <button onClick={runAnalysis} disabled={!file || busy}>
          {busy ? "Analysing…" : "Track ball"}
        </button>
      </div>

      {videoUrl ? (
        <>
          <p className="hint">
            {corners.length < 4
              ? `Pause on a clear frame, then click the ${CORNER_NAMES[corners.length]} corner of the court (${corners.length + 1} of 4).`
              : calibration
                ? "Court calibrated."
                : "Calibrating…"}
          </p>
          <div className="stage">
            <video ref={videoRef} src={videoUrl} controls playsInline />
            <canvas ref={canvasRef} />
            {corners.length < 4 && <div className="picker" onClick={onPick} />}
          </div>
        </>
      ) : (
        <p className="hint">Choose a clip filmed from behind the baseline to get started.</p>
      )}

      {error && <p className="error">{error}</p>}
      {analysis && (
        <p className="hint">
          Ball found in {detected} of {analysis.frames.length} frames ({analysis.fps.toFixed(0)} fps).
        </p>
      )}
    </main>
  );
}
