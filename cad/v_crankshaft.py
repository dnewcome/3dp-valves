"""v_crankshaft.py — the single VERTICAL drive shaft. One motor turns it; a shared crank
throw at the cylinder plane reciprocates the two opposed pistons 180deg out of phase, and
the shaft top keys into the rotary-distributor rotor above -- so the SAME shaft drives both
the pistons and the output "cam", coaxially (no right-angle take-off).
    python cad/v_crankshaft.py -> build/v_crankshaft.stl   (built at crank angle phi=0)

Built in world Z (shaft on the Z axis). Motor couples at the BOTTOM (a sealed submersible
unit), so the output can rise straight up the center above the rotor. Rotating the whole
shaft = advancing phi.
"""
import os
from build123d import *
from vpump_params import (SHAFT_D, THROW, CYL_Z, ROTOR_Z0, VALVE_Z, EPS, Pos, Rot)

PHI_BUILD    = 0.0
CRANKPIN_D   = 7.0
WEB_D        = 24.0
COUPLING_D   = 12.0
SHAFT_BOT    = -12.0            # motor-coupling end (below the block)
SHAFT_TOP    = ROTOR_Z0 + 3.0  # keys into the rotor socket


def _zcyl(d, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)


def part(phi=PHI_BUILD):
    shaft = _zcyl(SHAFT_D, SHAFT_BOT, SHAFT_TOP)
    shaft = shaft.fuse(_zcyl(COUPLING_D, SHAFT_BOT, SHAFT_BOT + 8))         # motor coupling boss
    shaft = shaft.fuse(_zcyl(WEB_D, CYL_Z - 2, CYL_Z + 2))                  # crank web (disc)

    # shared crankpin (both opposed conrods wrap it), at radius THROW, angle phi
    px, py = THROW * cos_r(phi), THROW * sin_r(phi)
    shaft = shaft.fuse(_zcyl(CRANKPIN_D, CYL_Z - 6, CYL_Z + 6, x=px, y=py))
    return shaft


# tiny local trig so the module stays import-light
from math import radians as _r, cos as _c, sin as _s
def cos_r(d): return _c(_r(d))
def sin_r(d): return _s(_r(d))


MATES = {"pin": Pos(THROW, 0, CYL_Z)}       # crankpin at phi=0 (rotates with the shaft)


if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    export_stl(part(), "build/v_crankshaft.stl")
    import trimesh
    m = trimesh.load("build/v_crankshaft.stl")
    print("v_crankshaft:", (m.bounds[1] - m.bounds[0]).round(1),
          "bodies:", len(m.split(only_watertight=False)),
          "watertight:", m.is_watertight)
