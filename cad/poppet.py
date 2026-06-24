"""poppet.py — moving poppet for the NC solenoid valve. Grips the solenoid plunger
tip, carries a printable flat TPU disc gasket on its sealing face, and presents a
top annulus for the return spring. Dimensions are imported from solenoid_block so
the poppet always matches the chamber/seat it seals against.
    python cad/poppet.py -> build/poppet.stl

Seal: a flat TPU disc sits in a shallow bottom pocket and protrudes ~0.4mm to
compress against the Ø6 seat land (face seal). This is the most printable TPU
gasket. An O-ring GROOVE alternative would need a wider seat land (bump SEAT_OD in
solenoid_block to ~9) — noted for later.

Attachment: blind bore presses/glues onto the Ø8 plunger tip. Thin wall (~1.5mm)
so retain with adhesive or a plunger-tip detail; no set-screw boss (would intrude
into the 0.5mm chamber flow gap).
"""
import os
from build123d import *
from solenoid_block import CHAMBER_D, SEAT_OD, ORIFICE_D, PLUNGER_D

# ---- poppet head (rides in the chamber) ----
POPPET_CLEAR = 1.0                          # diametral clearance in chamber -> 0.5mm radial flow gap
POPPET_D     = CHAMBER_D - POPPET_CLEAR     # 11.0; annular gap area >> orifice area
POPPET_H     = 4.5                          # seated 13..17.5 leaves ~2.5mm chamber for return spring

# ---- plunger attachment (blind bore from the top) ----
PLUNGER_FIT     = 0.1                       # slip fit + adhesive
PLUNGER_BORE_D  = PLUNGER_D + PLUNGER_FIT   # 8.1
BORE_DEPTH      = 2.5

# ---- TPU disc seal pocket (bottom face) ----
SEAL_POCKET_D     = SEAT_OD + 1.0           # 7.0; captures a Ø7 flat TPU disc covering the land
SEAL_POCKET_DEPTH = 0.8                     # disc ~1.2mm thick -> protrudes ~0.4mm to compress

EPS = 0.5                                   # cut overshoot


def _zcyl(d, z0, z1):
    return Pos(0, 0, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)


def part():
    p = Cylinder(POPPET_D / 2, POPPET_H, align=(Align.CENTER, Align.CENTER, Align.MIN))

    plunger_bore = _zcyl(PLUNGER_BORE_D, POPPET_H - BORE_DEPTH, POPPET_H + EPS)   # open top
    seal_pocket  = _zcyl(SEAL_POCKET_D, -EPS, SEAL_POCKET_DEPTH)                  # open bottom

    p = p.cut(plunger_bore, seal_pocket)

    # sanity: web between bore floor and seal pocket must stay positive
    web = (POPPET_H - BORE_DEPTH) - SEAL_POCKET_DEPTH
    assert web > 0.8, f"web too thin: {web:.2f}mm"
    return p


if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    export_stl(part(), "build/poppet.stl")
    import trimesh
    m = trimesh.load("build/poppet.stl")
    print("poppet:", (m.bounds[1] - m.bounds[0]).round(1),
          "bodies:", len(m.split(only_watertight=False)),
          "watertight:", m.is_watertight)
