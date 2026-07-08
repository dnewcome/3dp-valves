"""crankshaft.py — the ONE shaft that runs the whole pump. A single motor turns it;
it reciprocates the two pistons 180 deg out of phase (two opposed throws) and drives the
S-tube swing off a third eccentric, so nothing needs its own actuator.
    python cad/crankshaft.py -> build/crankshaft.stl   (built at crank angle phi=PHI_BUILD)

Built in a LOCAL frame with the crank axis along X at the origin (y=0, z=0); the assembly
translates it to y=CRANK_Y (behind the block). Rotating the whole shaft = advancing phi.
The connecting rods and the swing pushrod are drawn at ASSEMBLY time as straight links
between the pin centers this shaft defines (their exact swing timing is a MuJoCo job --
see PUMP_BRIEF's open question), so this file is just the rotating iron.
"""
import os
from math import hypot, atan2, degrees
from build123d import *
from pump_params import (THROW, SHAFT_D, PITCH, PHASE, X_SWING, X_DRIVE, SWING_THROW,
                         SWING_DRIVE_PHASE, crank_offset, swing_offset, Pos, Rot)

PHI_BUILD = 0.0          # crank angle the exported STL is frozen at (+X piston at front dead center)
WEB_T     = 4.0          # crank cheek thickness
PIN_LEN   = 10.0         # crankpin length (conrod big-end width + clearance)
DRIVE_EXT = 12.0         # motor-coupling stub past the +X end
COUPLING_D = 12.0
CHEEK_R   = SHAFT_D / 2 + 2.0     # rounded end radius of a crank cheek


def _xcyl(d, x0, x1, y=0.0, z=0.0):
    """Cylinder with axis along X, spanning x0..x1, offset to (y, z)."""
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(d / 2, x1 - x0)


def _cheek(xw, dy, dz):
    """A thin crank cheek at x=xw: a rounded arm from the axis (0,0) out to the pin (dy,dz)."""
    axis = _xcyl(2 * CHEEK_R, xw - WEB_T / 2, xw + WEB_T / 2, 0, 0)
    pin  = _xcyl(2 * CHEEK_R, xw - WEB_T / 2, xw + WEB_T / 2, dy, dz)
    L, ang = hypot(dy, dz), degrees(atan2(dz, dy))
    bridge = Pos(xw, dy / 2, dz / 2) * Rot(ang, 0, 0) * Box(WEB_T, L, 2 * CHEEK_R)
    return axis.fuse(pin).fuse(bridge)


def _throw(xc, dy, dz, pin_len):
    """One crank throw at x=xc: two cheeks flanking an offset crankpin at (dy, dz)."""
    x0, x1 = xc - pin_len / 2, xc + pin_len / 2
    pin = _xcyl(SHAFT_D, x0, x1, y=dy, z=dz)
    return _cheek(x0, dy, dz).fuse(_cheek(x1, dy, dz)).fuse(pin)


def part(phi=PHI_BUILD):
    # continuous main journal down the whole axis (guarantees one connected, watertight body)
    shaft = _xcyl(SHAFT_D, X_SWING - WEB_T, X_DRIVE + DRIVE_EXT)

    # two opposed piston throws
    for sx in (-1, 1):
        dy, dz = crank_offset(PHASE[sx] + phi)
        shaft = shaft.fuse(_throw(sx * PITCH / 2, dy, dz, PIN_LEN))

    # swing eccentric (drives the S-tube pushrod)
    sdy, sdz = swing_offset(SWING_DRIVE_PHASE + phi)
    shaft = shaft.fuse(_throw(X_SWING, sdy, sdz, 8.0))

    # motor-coupling boss at the drive end
    shaft = shaft.fuse(_xcyl(COUPLING_D, X_DRIVE, X_DRIVE + DRIVE_EXT))
    return shaft


# ---- mate points (local frame; assembly adds Pos(0, CRANK_Y, 0)) ---------------------
MATES = {
    "drive": Pos(X_DRIVE + DRIVE_EXT, 0, 0) * Rot(0, 90, 0),   # +Z -> +X, motor couples here
}


if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    export_stl(part(), "build/crankshaft.stl")
    import trimesh
    m = trimesh.load("build/crankshaft.stl")
    print("crankshaft:", (m.bounds[1] - m.bounds[0]).round(1),
          "bodies:", len(m.split(only_watertight=False)),
          "watertight:", m.is_watertight)
