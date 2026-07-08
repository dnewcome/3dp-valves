"""s_tube.py — the SWING TUBE (S-valve): a gooseneck that pipes one cylinder port to
the on-axis discharge, and rocks about the discharge axis to alternate between the two
cylinders. This is why the pump eats beads: the only "valve" is a fat tube whose bore
(Ø TUBE_BORE) is 4x the design bead -- nothing small to jam.
    python cad/s_tube.py -> build/s_tube.stl

Local frame (the assembly rotates this about local Y to swing it):
  pivot / discharge axis = local Y through the origin.
  MOUTH at (0, 0, MOUTH_R): a flat annulus facing -Y that presses (via the wear ring)
    on a cylinder port. Rotating +/-SWING_A about Y swings the mouth between the two ports.
  gooseneck sweeps from the mouth forward (+Y) and inward to the axis at (0, TUBE_FWD, 0),
  then a straight DISCHARGE stub continues +Y along the axis (rotary-seals to the outlet).
Because the mouth rides a circle of radius MOUTH_R centered on the pivot axis, and the
plate is perpendicular to that axis, the mouth stays flat in the plate plane at every
swing angle -- exactly the property that lets one rigid tube seal two ports.
"""
import os
from build123d import *
from pump_params import (TUBE_BORE, TUBE_OD, MOUTH_R, MOUTH_Y, TUBE_FWD, DISCH_LEN, EPS,
                         Pos, Rot)


def _ycyl(d, y0, y1, x=0.0, z=0.0):
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(d / 2, y1 - y0)


def _gooseneck(dia):
    """Solid rod of diameter `dia` swept along the mouth->axis centerline."""
    path = Spline((0, MOUTH_Y, MOUTH_R), (0, TUBE_FWD, 0),
                  tangents=[(0, 1, 0), (0, 1, 0)])           # leaves & arrives along +Y
    sec = Plane(origin=(0, MOUTH_Y, MOUTH_R), z_dir=(0, 1, 0)) * Circle(dia / 2)
    return sweep(sec, path=path)


def part():
    # OUTER solid = gooseneck fused with the coaxial discharge stub (1mm overlap to fuse)
    outer = _gooseneck(TUBE_OD)
    outer = outer.fuse(_ycyl(TUBE_OD, TUBE_FWD - 1.0, TUBE_FWD + DISCH_LEN))

    # INNER solid = the bead-safe bore, same shape; overshoot the discharge end so it opens
    inner = _gooseneck(TUBE_BORE)
    inner = inner.fuse(_ycyl(TUBE_BORE, TUBE_FWD - 1.0, TUBE_FWD + DISCH_LEN + EPS))

    return outer.cut(inner)


# ---- mate points (local frame) -------------------------------------------------------
# +Z of each mate points OUT along the joining direction, origin on the contact face.
MATES = {
    "pivot":     Pos(0, 0, 0),                                       # discharge/swing axis origin
    "mouth":     Pos(0, MOUTH_Y, MOUTH_R) * Rot(90, 0, 0),          # +Z -> -Y (seats on a port)
    "discharge": Pos(0, TUBE_FWD + DISCH_LEN, 0) * Rot(-90, 0, 0),  # +Z -> +Y (outlet)
}


if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    export_stl(part(), "build/s_tube.stl")
    import trimesh
    m = trimesh.load("build/s_tube.stl")
    print("s_tube:", (m.bounds[1] - m.bounds[0]).round(1),
          "bodies:", len(m.split(only_watertight=False)),
          "watertight:", m.is_watertight)
