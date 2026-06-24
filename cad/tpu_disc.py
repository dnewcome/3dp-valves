"""tpu_disc.py — flat TPU sealing gasket for the poppet. Print in TPU (Shore ~95A).
Press-fits into the poppet's bottom seal pocket and protrudes to face-seal the
Ø6 seat land, blocking the orifice when the valve is closed. Dimensions follow the
poppet's pocket so the gasket always matches.
    python cad/tpu_disc.py -> build/tpu_disc.stl
"""
import os
from build123d import *
from poppet import SEAL_POCKET_D, SEAL_POCKET_DEPTH

DISC_FIT  = 0.3                              # snug press fit into the pocket
DISC_D    = SEAL_POCKET_D - DISC_FIT         # 6.7
PROTRUDE  = 0.4                              # stand-proud -> compresses on the seat land
DISC_H    = SEAL_POCKET_DEPTH + PROTRUDE     # 1.2 (0.8 in pocket + 0.4 proud)
# solid disc: it covers the Ø3 orifice when seated, so no center hole.


def part():
    return Cylinder(DISC_D / 2, DISC_H, align=(Align.CENTER, Align.CENTER, Align.MIN))


if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    export_stl(part(), "build/tpu_disc.stl")
    import trimesh
    m = trimesh.load("build/tpu_disc.stl")
    print("tpu_disc:", (m.bounds[1] - m.bounds[0]).round(1),
          "bodies:", len(m.split(only_watertight=False)),
          "watertight:", m.is_watertight)
