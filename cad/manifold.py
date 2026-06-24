"""manifold.py — 2-channel supply manifold base. One inlet feeds an internal gallery
that distributes to TWO top-face ports, each matching the shared PORT INTERFACE so a
solenoid_block bolts down on top with a TPU gasket (sitting in the groove cut here)
sealing the joint. This is the composition layer: the parametric schematic (1 inlet ->
2 independently-valved outlets) realized as one printable manifold.
    python cad/manifold.py -> build/manifold.stl

Generalizes trivially to N channels: extend `centers`.
"""
import os
from build123d import *
from interface import (TILE, PORT_D, BOLT_INSERT_D, GASKET_CL_D, GASKET_W,
                       GASKET_DEPTH, bolt_xy)

GAP       = 4.0                       # gap between mounted blocks
PITCH     = TILE + GAP               # 34: center-to-center spacing of channels
MAN_X     = PITCH + TILE             # 64: spans both tiles
MAN_Y     = TILE                     # 30
MAN_H     = 12.0

GALLERY_D = 5.0                       # common supply gallery bore
GALLERY_Z = 6.0                      # gallery centerline height

EPS = 0.6

# channel mount centers on the top face
centers = [(-PITCH / 2, 0.0), (PITCH / 2, 0.0)]


def _vcyl(d, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)


def _hcyl_x(d, x0, x1, z, y=0.0):
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(d / 2, x1 - x0)


def _gasket_ring(cx, cy):
    """Annular groove cut into the top face around a port at (cx, cy)."""
    outer = _vcyl(GASKET_CL_D + GASKET_W, MAN_H - GASKET_DEPTH, MAN_H + EPS, cx, cy)
    inner = _vcyl(GASKET_CL_D - GASKET_W, MAN_H - GASKET_DEPTH - EPS, MAN_H + 2 * EPS, cx, cy)
    return outer.cut(inner)


def part():
    body = Box(MAN_X, MAN_Y, MAN_H, align=(Align.CENTER, Align.CENTER, Align.MIN))

    cuts = []
    # single inlet = the gallery open end at the -X face; gallery runs under both ports
    cuts.append(_hcyl_x(GALLERY_D, -MAN_X / 2 - EPS, PITCH / 2 + 5.0, GALLERY_Z))

    rings = []
    for (cx, cy) in centers:
        # vertical port drop from top face down to the gallery
        cuts.append(_vcyl(PORT_D, GALLERY_Z - 1.0, MAN_H + EPS, cx, cy))
        # heat-set insert bores (through, so the iron doesn't bottom out)
        for (bx, by) in bolt_xy(cx, cy):
            cuts.append(Pos(bx, by, MAN_H / 2) * Cylinder(BOLT_INSERT_D / 2, MAN_H + 2 * EPS))
        rings.append(_gasket_ring(cx, cy))

    body = body.cut(*cuts)
    body = body.cut(*rings)
    return body


if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    export_stl(part(), "build/manifold.stl")
    import trimesh
    m = trimesh.load("build/manifold.stl")
    print("manifold:", (m.bounds[1] - m.bounds[0]).round(1),
          "bodies:", len(m.split(only_watertight=False)),
          "watertight:", m.is_watertight)
