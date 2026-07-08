"""v_rotor.py — the ROTARY DISTRIBUTOR plug: the "cam" that times the alternating output,
keyed to the vertical shaft so it turns with the drive. Because it rotates continuously,
each plate port is connected to the output for a fat ~160deg arc (the DWELL the horizontal
sim showed a plain eccentric can't give) and open to the bath the rest of the turn.
    python cad/v_rotor.py -> build/v_rotor.stl

Bottom face (rides on the valve plate at radius R_VALVE):
  OUTPUT kidney  (~160deg arc, +X side): connects the DISCHARGING port up through the
                 central output bore to the riser. Stops short of the rim -> sealed from bath.
  SUCTION relief (~160deg arc, opposite): connects the OTHER port out to the rim -> the
                 chamber (bath), so that cylinder draws fresh slurry. No check valves.
Center: a shaft socket (bottom) below the central output bore (top) -- shaft drives from
below, output exits up, so they never fight for the axis.
"""
import os
from math import radians, cos, sin
from build123d import *
from vpump_params import (ROTOR_D, ROTOR_H, R_VALVE, KIDNEY_W, KIDNEY_ARC, RISER_D,
                          SHAFT_D, EPS, Pos)


def _zcyl(d, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)


def _xcyl(d, x0, x1, z=0.0):
    return Pos((x0 + x1) / 2, 0, z) * Rot(0, 90, 0) * Cylinder(d / 2, x1 - x0)


def _arc_slot(r, dia, a0_deg, a1_deg, z0, z1, n=11):
    """A fused arc of vertical cylinders -> a robust kidney/relief slot."""
    sol = None
    for i in range(n):
        a = radians(a0_deg + (a1_deg - a0_deg) * i / (n - 1))
        c = _zcyl(dia, z0, z1, x=r * cos(a), y=r * sin(a))
        sol = c if sol is None else sol.fuse(c)
    return sol


def part():
    r = ROTOR_D / 2
    disc = Cylinder(r, ROTOR_H, align=(Align.CENTER, Align.CENTER, Align.MIN))   # z=0..ROTOR_H

    socket = _zcyl(SHAFT_D + 0.3, -EPS, 3.0)                      # shaft key socket (bottom)
    out_bore = _zcyl(RISER_D, 2.5, ROTOR_H + EPS)                 # central output bore (up, to riser)
    connector = _xcyl(RISER_D, 0.0, R_VALVE + 3.0, z=3.5)        # links the +X kidney to the output

    half = KIDNEY_ARC / 2
    # OUTPUT kidney: +X side, radius R_VALVE. Stops short of the rim (r=17 < 18) -> sealed from bath.
    kidney = _arc_slot(R_VALVE, KIDNEY_W, -half + 2, half - 2, -EPS, 4.5)
    # SUCTION relief: opposite side, pushed OUT past the rim (r=20 > 18) -> open to the bath.
    relief = _arc_slot(R_VALVE + 3.0, KIDNEY_W, 180 - half + 2, 180 + half - 2, -EPS, 3.0)

    return disc.cut(socket, out_bore, connector, kidney, relief)


MATES = {"kidney": Pos(R_VALVE, 0, 0)}      # kidney center at rotor-azimuth 0 (+X)


if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    export_stl(part(), "build/v_rotor.stl")
    import trimesh
    m = trimesh.load("build/v_rotor.stl")
    print("v_rotor:", (m.bounds[1] - m.bounds[0]).round(1),
          "bodies:", len(m.split(only_watertight=False)),
          "watertight:", m.is_watertight)
