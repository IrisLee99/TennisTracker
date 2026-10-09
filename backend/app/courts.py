"""Court dimensions for supported racket sports.

Court coordinates are in metres with the origin at the centre of the net:
x runs across the court (left to right as seen from the camera), y runs along
it (negative = near baseline, closest to the camera; positive = far baseline).
"""

from __future__ import annotations

from dataclasses import dataclass

Point = tuple[float, float]
Segment = tuple[Point, Point]


@dataclass(frozen=True)
class CourtSpec:
    name: str
    length_m: float
    width_m: float  # full (doubles) width, the outline used for calibration
    net_height_m: float
    extra_lines: tuple[Segment, ...] = ()

    @property
    def corners(self) -> list[Point]:
        """Outline corners in calibration order: far-left, far-right, near-right, near-left."""
        hw, hl = self.width_m / 2, self.length_m / 2
        return [(-hw, hl), (hw, hl), (hw, -hl), (-hw, -hl)]

    @property
    def lines(self) -> list[Segment]:
        c = self.corners
        outline = [(c[i], c[(i + 1) % 4]) for i in range(4)]
        net = ((-self.width_m / 2, 0.0), (self.width_m / 2, 0.0))
        return [*outline, net, *self.extra_lines]


def _tennis() -> CourtSpec:
    hl, single, service = 23.77 / 2, 8.23 / 2, 6.40
    return CourtSpec(
        name="tennis",
        length_m=23.77,
        width_m=10.97,
        net_height_m=0.914,
        extra_lines=(
            ((-single, -hl), (-single, hl)),
            ((single, -hl), (single, hl)),
            ((-single, service), (single, service)),
            ((-single, -service), (single, -service)),
            ((0.0, -service), (0.0, service)),
        ),
    )


def _pickleball() -> CourtSpec:
    hw, hl, kitchen = 6.10 / 2, 13.41 / 2, 2.13
    return CourtSpec(
        name="pickleball",
        length_m=13.41,
        width_m=6.10,
        net_height_m=0.864,
        extra_lines=(
            ((-hw, kitchen), (hw, kitchen)),
            ((-hw, -kitchen), (hw, -kitchen)),
            ((0.0, kitchen), (0.0, hl)),
            ((0.0, -kitchen), (0.0, -hl)),
        ),
    )


def _padel() -> CourtSpec:
    hw, service = 10.0 / 2, 6.95
    return CourtSpec(
        name="padel",
        length_m=20.0,
        width_m=10.0,
        net_height_m=0.88,
        extra_lines=(
            ((-hw, service), (hw, service)),
            ((-hw, -service), (hw, -service)),
            ((0.0, -service), (0.0, service)),
        ),
    )


COURTS: dict[str, CourtSpec] = {c.name: c for c in (_tennis(), _pickleball(), _padel())}
