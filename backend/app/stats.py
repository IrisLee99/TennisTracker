"""Shot statistics from ground-plane events.

v1 uses two points that sit on the court plane and so can be measured with the
homography alone: where the hitter's feet were at contact, and where the ball
bounced. That gives average horizontal speed and direction for the shot. It
underestimates peak (off-the-racket) speed, since the ball slows in flight;
the planned 3D trajectory fit replaces this.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .courts import Point


@dataclass(frozen=True)
class GroundEvent:
    t: float  # seconds
    position: Point  # court metres


@dataclass(frozen=True)
class ShotStats:
    distance_m: float
    duration_s: float
    speed_kmh: float
    angle_deg: float  # 0 = straight down the court, positive = towards +x


def shot_stats(hit: GroundEvent, bounce: GroundEvent) -> ShotStats:
    duration = bounce.t - hit.t
    if duration <= 0:
        raise ValueError("Bounce must come after the hit")
    dx = bounce.position[0] - hit.position[0]
    dy = bounce.position[1] - hit.position[1]
    distance = math.hypot(dx, dy)
    return ShotStats(
        distance_m=distance,
        duration_s=duration,
        speed_kmh=distance / duration * 3.6,
        angle_deg=math.degrees(math.atan2(dx, abs(dy))),
    )
