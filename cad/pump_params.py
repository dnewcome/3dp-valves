"""pump_params.py — SINGLE SOURCE OF TRUTH for the twin-cylinder S-valve pump.
Every dimension a pump part or the pump assembly shares lives here and is imported,
never re-typed (the pump analog of interface.py for the valve blocks). Also holds the
`place()` mate helper and the clog-safety guard.

WHY THIS PUMP: concrete pumps move fluid full of rocks because the only "valve" is a
FAT TUBE whose bore is bigger than any rock (the swinging S-tube). We copy that so glass
beads in mineral oil never meet a passage smaller than themselves. The whole geometry is
therefore governed by ONE rule enforced below: min wetted passage >= SAFETY * BEAD_D.

Coordinate frame (shared by every pump part + the assembly):
  +Y = discharge / pivot axis, points OUT the front of the pump.
  wear plate at y=0 (spans X-Z); cylinders behind it (-Y), hopper in front (+Y).
  two cylinder ports on the plate at (x = +/-PITCH/2, z = 0).
  S-tube pivot (discharge) axis runs along Y at (x = 0, z = -ZPIVOT), BELOW the block.
  S-tube rotates about that axis by +/-SWING_A to swing its mouth between the two ports.
"""
from math import hypot, degrees, atan2, radians, cos, sin, sqrt
from build123d import Location, Pos, Rot   # noqa: F401  (re-exported for parts)

# ======================================================================================
# Solids to pump (the design driver)
# ======================================================================================
BEAD_D  = 3.0      # design-MAX bead diameter [mm]. Real glass reflective beads are much
                   # smaller (paint-grade ~0.1-0.85, decorative up to ~2-3); 3.0 is a
                   # conservative ceiling. Bump this and rebuild to size up for coarser media.
SAFETY  = 3.0      # every bead-wetted passage must be >= SAFETY * BEAD_D (>= 9 mm here).

# ======================================================================================
# Cylinders (bores along Y, side by side in X, both centered at z=0)
# ======================================================================================
BORE_D   = 16.0    # cylinder bore (piston OD ~ this) -- huge vs a bead
WALL     = 4.0     # printed wall around a bore
PITCH    = 24.0    # center-to-center of the two cylinders (inter-bore wall = PITCH-BORE_D = 8)
STROKE   = 20.0    # piston stroke; crank throw = STROKE/2
THROW    = STROKE / 2
CYL_LEN  = 52.0    # bore depth behind the wear plate (holds stroke + piston + suction room)

# ======================================================================================
# Wear plate + ports (front face of the block, at y=0)
# ======================================================================================
PLATE_T  = 6.0     # wear-plate thickness (front slab of the block)
PORT_D   = 12.0    # port through the plate = the tube bore (gives a flat sealing LAND for
                   # the wear ring, and sets the min wetted passage). Bore 16 necks to 12 here.

# ======================================================================================
# S-tube (the swing valve) -- a gooseneck sweeping port -> discharge
# ======================================================================================
TUBE_BORE = 12.0   # bead-safe flow bore through the swing tube (== PORT_D; no constriction)
TUBE_WALL = 2.5
TUBE_OD   = TUBE_BORE + 2 * TUBE_WALL      # 17.0
ZPIVOT    = 28.0   # pivot/discharge axis sits this far BELOW the cylinder centerline (z=0)
TUBE_FWD  = 30.0   # how far the gooseneck reaches forward (+Y) into the hopper before the
                   # discharge turns back onto the axis
DISCH_LEN = 14.0   # straight discharge stub past the pivot (rotary-seals to the outlet collar)

# derived swing geometry -- the mouth rides a circle of radius MOUTH_R about the pivot axis
MOUTH_R = hypot(PITCH / 2, ZPIVOT)                 # 30.46: pivot -> a port
SWING_A = degrees(atan2(PITCH / 2, ZPIVOT))        # 23.2 deg: half-swing (port sits at +/-this)

# ======================================================================================
# Wear ring (replaceable TPU face seal on the S-tube mouth)
# ======================================================================================
RING_OD       = TUBE_OD                 # matches the tube mouth
RING_BORE     = TUBE_BORE               # bead-safe
RING_T        = 2.5                     # ring thickness (== the mouth->plate gap it fills)
RING_PROTRUDE = 0.5                     # printed proud of the gap -> squishes onto the plate to seal
MOUTH_Y       = RING_T                  # tube mouth sits this far forward (+Y) of the plate; ring fills it

# ======================================================================================
# Drive: one crankshaft behind the block (axis along X), two piston throws 180 deg apart
# ======================================================================================
SHAFT_D      = 8.0                       # crankshaft journal diameter
CONROD_LEN   = 46.0                      # big-end (crank) to small-end (wrist pin) length
WRIST_D      = 5.0                       # wrist-pin diameter (piston <-> conrod)
# crank axis behind the block; chosen so the crown ~kisses the plate at front dead center
# (crown_FDC = CRANK_Y + THROW + CONROD_LEN + crown_above_wrist(=10) ~= -6 == plate back).
CRANK_Y      = -72.0
SWING_THROW  = 12.0                      # crank eccentric throw that drives the S-tube swing
SWING_ARM    = 22.0                      # lever length from the pivot to the swing-pushrod pin
SWING_DRIVE_PHASE = 90.0                 # swing eccentric phase vs the main crank (a render/timing knob)
X_SWING      = -(PITCH / 2 + BORE_D + 8.0)   # swing eccentric sits outboard of the -X cylinder
X_DRIVE      = +(PITCH / 2 + BORE_D + 8.0)   # motor-coupling end, outboard of the +X cylinder

# hopper shell (open-top box in front of the plate, holds the slurry + the swinging tube)
HOP_WALL   = 3.0
HOP_FRONT  = TUBE_FWD + DISCH_LEN + 6.0  # +Y depth needed to clear the tube + discharge
HOP_TOP    =  BORE_D / 2 + WALL + 6.0    # open rim height above z=0
HOP_BOT    = -(ZPIVOT + TUBE_OD / 2 + HOP_WALL + 3.0)  # floor below the pivot

BLOCK_X = PITCH + BORE_D + 2 * WALL      # 48: block spans both cylinders + walls
BLOCK_Z = BORE_D + 2 * WALL              # 24: cylinders centered at z=0

EPS = 0.6                                # standard boolean overshoot for through-cuts


# ---- drive kinematics (shared by crankshaft.py + the assembly) -----------------------
# Crank axis along X at (y=CRANK_Y, z=0). A crankpin at angle phi is offset (dy,dz) in the
# Y-Z plane; the conrod (length CONROD_LEN) drives the wrist pin along the cylinder's Y axis.
def crank_offset(phi_deg):
    """(dy, dz) of a crankpin from the crank axis, at shaft angle phi."""
    a = radians(phi_deg)
    return (THROW * cos(a), THROW * sin(a))


def wrist_y(phi_deg):
    """World Y of the wrist pin (piston) for a cylinder whose crankpin is at angle phi,
    accounting for conrod angularity so the render is honest."""
    a = radians(phi_deg)
    return CRANK_Y + THROW * cos(a) + sqrt(CONROD_LEN ** 2 - (THROW * sin(a)) ** 2)


def swing_offset(phi_deg):
    """(dy, dz) of the swing eccentric pin from the crank axis, at shaft angle phi."""
    a = radians(phi_deg)
    return (SWING_THROW * cos(a), SWING_THROW * sin(a))


# The two cylinders run 180 deg out of phase: +X leads, -X trails by half a turn.
PHASE = {+1: 0.0, -1: 180.0}


# ---- mate helper (from the build123d-machine skill) ----------------------------------
def place(solid, frm: Location, onto: Location):
    """Snap `solid` so its local mate `frm` coincides with world mate `onto`."""
    return (onto * frm.inverse()) * solid


# ---- clog-safety guard: the whole point of the design -------------------------------
MIN_PASSAGE = min(BORE_D, PORT_D, TUBE_BORE)      # narrowest bead-wetted passage
assert MIN_PASSAGE >= SAFETY * BEAD_D, (
    f"CLOG RISK: min passage {MIN_PASSAGE:.1f}mm < {SAFETY}x bead {BEAD_D}mm "
    f"= {SAFETY * BEAD_D:.1f}mm. Widen the bore/port/tube or shrink BEAD_D.")


def _report():
    print("pump_params:",
          f"bead<= {BEAD_D}  min-passage {MIN_PASSAGE:.1f} ({MIN_PASSAGE / BEAD_D:.1f}x)",
          f"| bore {BORE_D} pitch {PITCH} stroke {STROKE}",
          f"| tube-bore {TUBE_BORE} mouth-R {MOUTH_R:.1f} swing +/-{SWING_A:.1f}deg")


if __name__ == "__main__":
    _report()
