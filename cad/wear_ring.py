"""wear_ring.py — replaceable TPU face seal on the S-tube mouth (print in TPU ~95A).
Bonds to the flat mouth annulus and stands slightly proud so it squishes onto the wear
plate, sealing mineral oil around the port while beads sweep across it. Loaded by the
discharge pressure itself (self-sealing) -- and because glass-in-oil is lubricating, it
grinds far less than glass dry or in water. This is the pump's designated WEAR ITEM:
print spares and swap it, exactly like the valve's tpu_disc.
    python cad/wear_ring.py -> build/wear_ring.stl

Authored centered at the origin (a clean printable washer). `at_mouth()` returns it
positioned on the tube mouth *in s_tube-local coordinates*, so the assembly can apply
the same swing transform to tube and ring together.
"""
import os
from build123d import *
from pump_params import (RING_OD, RING_BORE, RING_T, RING_PROTRUDE, MOUTH_R, MOUTH_Y,
                         EPS, Pos, Rot)

T = RING_T + RING_PROTRUDE                     # printed thickness (proud by RING_PROTRUDE)


def part():
    ring = Cylinder(RING_OD / 2, T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    bore = Pos(0, 0, -EPS) * Cylinder(RING_BORE / 2, T + 2 * EPS,
                                      align=(Align.CENTER, Align.CENTER, Align.MIN))
    return ring.cut(bore)


def at_mouth():
    """The ring placed on the S-tube mouth, in s_tube LOCAL coordinates (bond face to the
    mouth at y=MOUTH_Y, pressing face toward the plate at y=0, proud by RING_PROTRUDE)."""
    return Pos(0, MOUTH_Y, MOUTH_R) * Rot(90, 0, 0) * part()


MATES = {"seat": Pos(0, 0, T)}                 # top face bonds to the tube mouth


if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    export_stl(part(), "build/wear_ring.stl")
    import trimesh
    m = trimesh.load("build/wear_ring.stl")
    print("wear_ring:", (m.bounds[1] - m.bounds[0]).round(1),
          "bodies:", len(m.split(only_watertight=False)),
          "watertight:", m.is_watertight)
