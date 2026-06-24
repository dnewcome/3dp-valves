"""solenoid_block.py — single-channel direct-acting NC poppet solenoid valve BODY.
Houses a separate plunger+poppet (with TPU seal) and a 12V push-pull solenoid
(Makermotor PN00121 class: ~8mm plunger, ~10mm stroke). Direct-acting, normally
closed: return spring pushes the poppet onto the seat; energizing the coil lifts it.
    python cad/solenoid_block.py -> build/solenoid_block.stl

Now uses the shared bottom-face PORT INTERFACE (interface.py): inlet enters the
BOTTOM face on the central axis, coaxial with orifice/plunger/coil (valve-island
style), so the block bolts down onto a manifold with a TPU gasket sealing the joint.
The block bottom is a FLAT land; the gasket groove lives on the manifold.

Flow: bottom inlet -> vertical orifice -> seat land -> chamber -> outlet(+X).
The chamber->guide step is the return-spring upper seat. The coil bore pole sits
just above the plunger so the magnetic gap is SMALLEST when the poppet is seated.
"""
import os
from build123d import *
from interface import TILE, PORT_D, BOLT_CLEAR_D, bolt_xy

# ---- block envelope ----
BH = 43.0                          # block height (raised from 40 to give the spring room)

# ---- bottom inlet (shared interface) ----
SUPPLY_Z_TOP = 10.0                # inlet bore (Ø PORT_D) rises bottom..here, then necks to orifice

# ---- seat / orifice ----
ORIFICE_D    = 3.0                 # flow orifice; 100psi x area ~= 4.5N seating demand
SEAT_OD      = 6.0                 # flat sealing land OD (TPU poppet seats here)
SEAT_FLOOR_Z = 12.0                # chamber floor height
SEAT_RAISE   = 1.0                 # land protrudes this far into the chamber

# ---- valve chamber (poppet lift space, flow path to outlet) ----
CHAMBER_D     = 12.0               # poppet OD ~11 -> ~0.5mm annular flow gap
CHAMBER_TOP_Z = 23.0               # chamber spans SEAT_FLOOR_Z..here; ceiling = spring seat
OUTLET_Z      = 16.0              # outlet bore centerline (+X face), into chamber

# ---- plunger guide ----
PLUNGER_D   = 8.0                  # reference: the solenoid plunger diameter
GUIDE_D     = 8.3                  # slip fit around plunger
GUIDE_TOP_Z = 33.0                 # guide spans CHAMBER_TOP_Z..here

# ---- coil / solenoid mounting bore (MEASURE YOUR SOLENOID, then update) ----
COIL_BORE_D = 22.0                 # solenoid can/frame seats in this bore; spans GUIDE_TOP_Z..BH

EPS = 0.6                          # through-cut overshoot


def _zcyl(d, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)


def _xcyl(d, x0, x1, z):
    return Pos((x0 + x1) / 2, 0, z) * Rot(0, 90, 0) * Cylinder(d / 2, x1 - x0)


def part():
    body = Box(TILE, TILE, BH, align=(Align.CENTER, Align.CENTER, Align.MIN))

    chamber  = _zcyl(CHAMBER_D, SEAT_FLOOR_Z, CHAMBER_TOP_Z)
    guide    = _zcyl(GUIDE_D, CHAMBER_TOP_Z, GUIDE_TOP_Z)
    coilbore = _zcyl(COIL_BORE_D, GUIDE_TOP_Z, BH + EPS)            # open through top
    supply   = _zcyl(PORT_D, -EPS, SUPPLY_Z_TOP)                    # bottom inlet, open bottom
    outlet   = _xcyl(PORT_D, -1.0, TILE / 2 + EPS, OUTLET_Z)        # center to +X face

    holes = [Pos(x, y, BH / 2) * Cylinder(BOLT_CLEAR_D / 2, BH + 2 * EPS)
             for (x, y) in bolt_xy()]

    body = body.cut(chamber, guide, coilbore, supply, outlet, *holes)

    # raised sealing land, welded 1mm into the chamber floor (>=1mm overlap to fuse)
    land = _zcyl(SEAT_OD, SEAT_FLOOR_Z - 1.0, SEAT_FLOOR_Z + SEAT_RAISE)
    body = body.fuse(land)

    # orifice last: drills through the land and connects down to the supply bore
    orifice = _zcyl(ORIFICE_D, SUPPLY_Z_TOP - EPS, SEAT_FLOOR_Z + SEAT_RAISE + EPS)
    body = body.cut(orifice)

    return body


if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    export_stl(part(), "build/solenoid_block.stl")
    import trimesh
    m = trimesh.load("build/solenoid_block.stl")
    print("solenoid_block:", (m.bounds[1] - m.bounds[0]).round(1),
          "bodies:", len(m.split(only_watertight=False)),
          "watertight:", m.is_watertight)
