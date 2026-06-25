"""solenoid_block.py — single-channel direct-acting NC poppet solenoid valve BODY.
Houses a separate plunger+poppet (with TPU seal) and a 12V push-pull solenoid
(Makermotor PN00121 class: ~8mm plunger, ~10mm stroke).
    python cad/solenoid_block.py -> build/solenoid_block.stl

PRESSURE-TO-CLOSE layout: supply pressure fills the chamber and pushes the poppet
ONTO the seat, so pressure helps seal. The return spring only has to reseat the
poppet at zero pressure (light spring). The solenoid pulls the poppet UP to open,
against P x orifice-area + spring -- and it pulls from the seated position where the
magnetic gap is smallest and coil force is greatest. (See BRIEF.md for the force
balance and why this beats pressure-to-open.)

Flow:
  bottom inlet (manifold) -> off-axis riser -> CHAMBER (supply, surrounds poppet)
  CHAMBER --(poppet lifts off seat)--> orifice -> +X OUTLET
Supply path runs up the -X side; the outlet exits +X; both lie in the XZ plane so
they show in the Y=0 section. Coil bore pole sits just above the seated plunger.
"""
import os
from build123d import *
from interface import TILE, PORT_D, BOLT_CLEAR_D, bolt_xy

# ---- block envelope ----
BH = 43.0                          # block height

# ---- seat / orifice (on the central axis; orifice now drains DOWN to the outlet) ----
ORIFICE_D    = 3.0                 # flow orifice; sets P x A the coil must open against
SEAT_OD      = 6.0                 # flat sealing land OD (TPU poppet seats here)
SEAT_FLOOR_Z = 12.0                # chamber floor height
SEAT_RAISE   = 1.0                 # land protrudes this far into the chamber

# ---- valve chamber (= supply plenum; poppet lift space) ----
CHAMBER_D     = 12.0               # poppet OD ~11 -> ~0.5mm annular flow gap
CHAMBER_TOP_Z = 23.0               # chamber spans SEAT_FLOOR_Z..here; ceiling = spring seat

# ---- outlet (+X side, fed by the orifice) ----
OUTLET_Z = 7.0                     # outlet bore centerline; orifice drops into it

# ---- bottom inlet + off-axis supply riser into the chamber ----
SUP_PORT_TOP = 3.0                 # bottom port (Ø PORT_D, manifold interface) rises 0..here
SUP_JOG_Z    = 1.5                 # horizontal jog height connecting port -> riser
RISER_X      = -9.0                # riser sits in the -X wall, clear of chamber + bolts
RISER_D      = 3.5
FEED_Z       = 20.0                # radial feed pierces the chamber wall above the poppet
FEED_D       = 3.0

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

    # supply: bottom port -> jog -> riser -> radial feed into the chamber (all -X side)
    sup_port = _zcyl(PORT_D, -EPS, SUP_PORT_TOP)                    # bottom inlet, open bottom
    sup_jog  = _xcyl(RISER_D, RISER_X, 0.5, SUP_JOG_Z)             # port -> riser
    sup_riser = _zcyl(RISER_D, 1.0, FEED_Z + 1.0, x=RISER_X)
    sup_feed = _xcyl(FEED_D, RISER_X, -2.5, FEED_Z)                # riser -> chamber

    # outlet: +X side bore fed by the orifice
    outlet = _xcyl(PORT_D, -0.5, TILE / 2 + EPS, OUTLET_Z)

    holes = [Pos(x, y, BH / 2) * Cylinder(BOLT_CLEAR_D / 2, BH + 2 * EPS)
             for (x, y) in bolt_xy()]

    body = body.cut(chamber, guide, coilbore, sup_port, sup_jog, sup_riser,
                    sup_feed, outlet, *holes)

    # raised sealing land, welded 1mm into the chamber floor (>=1mm overlap to fuse)
    land = _zcyl(SEAT_OD, SEAT_FLOOR_Z - 1.0, SEAT_FLOOR_Z + SEAT_RAISE)
    body = body.fuse(land)

    # orifice last: through the land, draining DOWN into the +X outlet bore
    orifice = _zcyl(ORIFICE_D, OUTLET_Z - 0.5, SEAT_FLOOR_Z + SEAT_RAISE + EPS)
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
