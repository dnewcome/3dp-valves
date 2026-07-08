"""v_block.py — body of the VERTICAL submersible pump. Two OPPOSED cylinders (bores along
X, ports at the outer ends), a central vertical shaft bore + crank cavity, 90deg discharge
galleries that route each outer port UP and inward to a 2-port valve plate, and the valve
chamber the rotary distributor turns in. The chamber is also the suction plenum (vented to
the bath), so the cylinder NOT connected to the output draws fresh slurry from around the
submerged pump -- no check valves to clog.
    python cad/v_block.py -> build/v_block.stl

Flow (per cylinder): bore (horizontal) -> outer port -> UP -> inward -> UP -> plate port
-> [rotor kidney] -> central output riser. Net 90deg: horizontal cylinders, vertical out.
"""
import os
from math import hypot
from build123d import *
from vpump_params import (BLK_X, BLK_Y, BLK_Z0, BLK_Z1, BORE_D, PORT_D, PORT_X, BORE_INNER_X,
                          CYL_Z, CRANK_CAV_D, SHAFT_D, GAL_Z, R_VALVE, VALVE_Z, ROTOR_BORE,
                          CHAMBER_TOP, WALL, EPS, Pos, Rot)


def _zcyl(d, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)


def _xcyl(d, x0, x1, z, y=0.0):
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(d / 2, x1 - x0)


def _ycyl(d, y0, y1, x=0.0, z=0.0):
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(d / 2, y1 - y0)


def _gallery(sx):
    """Discharge passage for one cylinder (sx=+/-1): a single straight bore that taps the
    bore's outer end and rises inward to the valve-plate port -- turning the horizontal
    cylinder flow up to the coaxial vertical valve (net 90deg: horizontal in, vertical out).
    Straight (not an elbow) keeps the boolean clean/watertight; taps 4mm inside the bore."""
    xo, zo = sx * (PORT_X - 4.0), CYL_Z             # tap, inside the bore's outer end
    xv, zv = sx * R_VALVE, VALVE_Z                  # plate port on the chamber floor
    L = hypot(xv - xo, zv - zo)
    mid = ((xo + xv) / 2, 0, (zo + zv) / 2)
    d = ((xv - xo) / L, 0, (zv - zo) / L)
    return Plane(origin=mid, z_dir=d) * Cylinder(PORT_D / 2, L + 6.0)


def part():
    body = Box(BLK_X, BLK_Y, BLK_Z1 - BLK_Z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = Pos(0, 0, BLK_Z0) * body

    cuts = []
    # opposed cylinder bores (open at the inner end into the crank cavity)
    for sx in (-1, 1):
        cuts.append(_xcyl(BORE_D, min(sx * 6.0, sx * PORT_X), max(sx * 6.0, sx * PORT_X), z=CYL_Z))
        cuts.append(_gallery(sx))

    cuts.append(_zcyl(CRANK_CAV_D, 16.0, 36.0))                    # central crank cavity
    cuts.append(_zcyl(SHAFT_D + 1.0, BLK_Z0 - EPS, VALVE_Z + 1.0))  # vertical shaft bore
    cuts.append(_zcyl(ROTOR_BORE, VALVE_Z, CHAMBER_TOP + EPS))     # valve chamber (open at top)

    body = body.cut(*cuts)
    # bath vents (suction plenum -> bath): a Ø PORT_D through-hole across the thick X ends
    # into the chamber, so the non-selected cylinder draws from the surrounding fluid.
    body = body.cut(_xcyl(PORT_D, -BLK_X / 2 - EPS, BLK_X / 2 + EPS, z=52.0))
    return body


# ---- mate points (local frame) -------------------------------------------------------
MATES = {
    "port_pos":  Pos(+R_VALVE, 0, VALVE_Z),        # +X cylinder's plate port
    "port_neg":  Pos(-R_VALVE, 0, VALVE_Z),        # -X cylinder's plate port
    "shaft":     Pos(0, 0, CYL_Z),                 # crank plane on the shaft axis
    "rotor_seat": Pos(0, 0, VALVE_Z),              # rotor sits on the plate here
}


if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    export_stl(part(), "build/v_block.stl")
    import trimesh
    m = trimesh.load("build/v_block.stl")
    print("v_block:", (m.bounds[1] - m.bounds[0]).round(1),
          "bodies:", len(m.split(only_watertight=False)),
          "watertight:", m.is_watertight)
