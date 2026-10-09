export type Point = [number, number];
export type Segment = [Point, Point];

export interface Calibration {
  sport: string;
  image_to_court: number[][];
  court_lines: Segment[];
}

export interface FrameResult {
  t: number;
  ball: Point | null;
}

export interface VideoAnalysis {
  fps: number;
  width: number;
  height: number;
  frames: FrameResult[];
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export function calibrate(sport: string, corners: Point[]): Promise<Calibration> {
  return fetch("/api/calibrate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sport, corners }),
  }).then((r) => json<Calibration>(r));
}

export function analyze(video: File): Promise<VideoAnalysis> {
  const form = new FormData();
  form.append("video", video);
  return fetch("/api/analyze", { method: "POST", body: form }).then((r) => json<VideoAnalysis>(r));
}
