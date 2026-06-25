"""solenoid_model.py — REFERENCE model of the off-the-shelf 12V push-pull solenoid
(Makermotor PN00121 class). NOT printed — it's a stand-in so the assembly shows how
the bought solenoid seats in the coil bore and how its plunger reaches the poppet.
    python cad/solenoid_model.py -> build/solenoid_coil.stl, build/solenoid_plunger.stl

Built in solenoid_block LOCAL coordinates (same z datum as the block) so the assembly
can place it with the block's transform. Update CAN_OD / COIL_LEN to your real part.
"""
import os
from build123d import *
from solenoid_block import (PLUNGER_D, COIL_BORE_D, GUIDE_TOP_Z, BH,
                            SEAT_FLOOR_Z, SEAT_RAISE)
from poppet import POPPET_H, BORE_DEPTH

# where the poppet sits (block-local z), so the plunger tip lands in the poppet bore
SEAT_TOP       = SEAT_FLOOR_Z + SEAT_RAISE          # 13
POPPET_BOTTOM  = SEAT_TOP + 0.4                      # +0.4 disc protrusion
POPPET_TOP     = POPPET_BOTTOM + POPPET_H            # 17.9
PLUNGER_TIP_Z  = POPPET_TOP - BORE_DEPTH             # 15.4 (bottoms in poppet bore)

# coil can: seats on the guide/coil-bore ledge and protrudes above the block top
COIL_BOTTOM_Z = GUIDE_TOP_Z                          # 33
COIL_LEN      = 28.0
COIL_TOP_Z    = COIL_BOTTOM_Z + COIL_LEN             # 61
CAN_OD        = COIL_BORE_D - 0.3                     # 21.7 slip fit into the bore
CAN_BORE_D    = PLUNGER_D + 0.6                       # 8.6 (plunger slides through)

# plunger / armature
PLUNGER_OD    = PLUNGER_D - 0.2                       # 7.8 (slides in the Ø8.3 guide)
PLUNGER_TOP_Z = COIL_TOP_Z - 6.0                     # ends inside the can

LEAD_D        = 1.6
EPS           = 0.6


def _zcyl(d, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)


def coil():
    can = _zcyl(CAN_OD, COIL_BOTTOM_Z, COIL_TOP_Z)
    can = can.cut(_zcyl(CAN_BORE_D, COIL_BOTTOM_Z - EPS, COIL_TOP_Z + EPS))
    # two wire leads out the top (cosmetic, so it reads as a solenoid)
    for lx in (-7.0, 7.0):
        can = can.fuse(_zcyl(LEAD_D, COIL_TOP_Z - 1.0, COIL_TOP_Z + 8.0, x=lx))
    return can


def plunger():
    return _zcyl(PLUNGER_OD, PLUNGER_TIP_Z, PLUNGER_TOP_Z)


if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    import trimesh
    for name, shape in (("solenoid_coil", coil()), ("solenoid_plunger", plunger())):
        export_stl(shape, f"build/{name}.stl")
        m = trimesh.load(f"build/{name}.stl")
        print(f"{name}:", (m.bounds[1] - m.bounds[0]).round(1),
              "bodies:", len(m.split(only_watertight=False)),
              "watertight:", m.is_watertight)
