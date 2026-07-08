"""vpump_params.py — SOURCE OF TRUTH for the VERTICAL, submersible S-valve pump variant.
Same bead-safe philosophy as the horizontal pump (constants reused from pump_params), but
re-packaged around a VERTICAL drive shaft so the pump can run submerged with the motor out
of the fluid, and the alternating-output valve becomes a ROTARY DISTRIBUTOR coaxial with
the shaft -- which gives the DWELL that the horizontal sim showed a plain eccentric lacks.

Layout (Z = vertical, up; shaft on the Z axis):
  top     ─ output RISER (up to the surface) + motor coupling
  valve   ─ rotary distributor ROTOR keyed to the shaft, over a 2-port valve plate.
            A ~160deg kidney connects the DISCHARGING cylinder's port up to the riser and
            leaves the other port open to the bath (suction). Rotation = the "cam".
  pump    ─ TWO OPPOSED cylinders (bores along X, ports at the outer ends), one central
            crank throw driving both pistons 180deg out of phase.
  90deg piping ─ each outer port turns UP and inward to its plate port, so the output ends
            up 90deg to the cylinders (vertical vs horizontal).

Opposed (not side-by-side) because a central vertical shaft makes collinear cylinders a
clean, zero-offset slider-crank with ports naturally 180deg apart for the rotary valve.
"""
from math import cos, sin, sqrt, radians, degrees
from pump_params import (BEAD_D, SAFETY, BORE_D, WALL, PORT_D, THROW, TUBE_BORE,
                         place, Pos, Rot)                                    # noqa: F401
from piston import PISTON_H, WRIST_Z, PISTON_D                              # reuse the piston

# ---- drive shaft (vertical) ----
SHAFT_D  = 8.0
CYL_Z    = 26.0        # cylinder centerline height (also the crank plane)
VCONROD  = 26.0        # conrod length -> stroke = 2*THROW = 20 (centered slider-crank, no offset)
CROWN    = PISTON_H - WRIST_Z            # how far the crown leads the wrist (10)

# ---- opposed cylinders (bores along X at y=0, z=CYL_Z) ----
BORE_INNER_X = 8.0                        # inner (crank-side) open end of each bore
PORT_X       = THROW + VCONROD + CROWN + 2.0     # 48: outer working end / gallery tap
CRANK_CAV_D  = 30.0                       # central cavity the bore inner ends open into (crank lives here)

# ---- 90deg discharge galleries: outer port -> up -> inward -> up to the plate ----
GAL_Z    = 40.0        # height the gallery runs inward at (clears the bore below)
R_VALVE  = 11.0        # plate-port radius = rotor kidney centerline radius (ports at (+/-R_VALVE, 0))
VALVE_Z  = 44.0        # valve plate (chamber floor)

# ---- rotary distributor ----
ROTOR_D     = 36.0
ROTOR_BORE  = ROTOR_D + 2.0               # valve-chamber bore the rotor turns in
ROTOR_Z0    = 45.0                        # rotor bottom (0.5 gap over the plate at 44 + shaft top)
ROTOR_H     = 9.0
KIDNEY_ARC  = 160.0                       # degrees: the dwell window (each port sealed ~160/180)
KIDNEY_W    = PORT_D                       # radial width of the kidney slot (bead-safe = PORT_D)
CHAMBER_TOP = 56.0

# ---- output riser (up to the surface) + submersion ----
RISER_D   = TUBE_BORE                     # 12, bead-safe
RISER_TOP = 72.0
WATERLINE = 62.0                          # everything below this runs submerged

# ---- block envelope (Y wide enough for the valve chamber) ----
BLK_X = 2 * (PORT_X + WALL)               # 104
BLK_Y = ROTOR_BORE + 2 * WALL             # 46
BLK_Z0, BLK_Z1 = 12.0, CHAMBER_TOP        # main wet body spans this Z range
EPS = 0.6


# ---- opposed-piston kinematics (shared central crankpin, radius THROW, at z=CYL_Z) ----
def wrist_x(phi_deg, sx):
    """World X of a piston wrist. sx=+1 -> +X cylinder (+root), sx=-1 -> -X cylinder (-root).
    Both driven by ONE crankpin at angle phi, so they run 180deg out of phase."""
    a = radians(phi_deg)
    return THROW * cos(a) + sx * sqrt(VCONROD ** 2 - (THROW * sin(a)) ** 2)


def discharging_side(phi_deg):
    """+1 if the +X cylinder is discharging (piston moving toward its +X port), else -1."""
    return +1 if wrist_x(phi_deg + 0.5, +1) > wrist_x(phi_deg - 0.5, +1) else -1


# the rotor is keyed to the shaft with this mounting phase so the kidney sits over a port
# during that cylinder's DISCHARGE stroke (+X port at az 0 discharges around phi=270).
ROTOR_PHASE = 90.0


def kidney_center_az(phi_deg):
    """World azimuth [deg] the rotor kidney points at, at shaft angle phi. Kidney is fixed on
    the rotor at rotor-azimuth 0, mounted with ROTOR_PHASE. Port A at az 0, port B at 180."""
    return (phi_deg + ROTOR_PHASE) % 360.0


def port_sealed(phi_deg, port_az):
    """True if the plate port at azimuth port_az is under the kidney (connected to output)."""
    d = abs(((kidney_center_az(phi_deg) - port_az + 180) % 360) - 180)   # angular distance
    return d <= KIDNEY_ARC / 2


def sealed_fraction(n=720):
    """Fraction of the cycle where the DISCHARGING port is connected to the output -- the
    same 'port coverage' metric the horizontal sim reports. The rotary distributor gets this
    for free from its kidney arc (vs ~41% for a plain sinusoidal eccentric)."""
    ok = 0
    for k in range(n):
        phi = 360.0 * k / n
        port_az = 0.0 if discharging_side(phi) > 0 else 180.0
        ok += port_sealed(phi, port_az)
    return ok / n


# ---- clog guard (same rule as the horizontal pump; the kidney slot counts too) ----
MIN_PASSAGE = min(BORE_D, PORT_D, TUBE_BORE, RISER_D, KIDNEY_W)
assert MIN_PASSAGE >= SAFETY * BEAD_D, (
    f"CLOG RISK: min passage {MIN_PASSAGE:.1f} < {SAFETY}x bead {BEAD_D}")


def _report():
    print("vpump_params:",
          f"min-passage {MIN_PASSAGE:.1f} ({MIN_PASSAGE/BEAD_D:.1f}x bead)",
          f"| opposed bores +/-{PORT_X:.0f}mm | valve R{R_VALVE} kidney {KIDNEY_ARC:.0f}deg",
          f"| discharging-port sealed {sealed_fraction()*100:.0f}% of the cycle "
          f"(vs ~41% for a plain sinusoidal eccentric)")


if __name__ == "__main__":
    _report()
