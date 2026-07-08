"""piston.py — piston that reciprocates in a cylinder bore, pushing bead-laden oil out
through the port on the forward stroke and drawing slurry from the hopper on the return.
Carries an O-ring in a radial gland (the running seal against the bore) and a rear
CLEVIS with a wrist-pin bore for the connecting rod. Bore/geometry follow cylinder_block
so the piston always matches the cylinder it runs in.
    python cad/piston.py -> build/piston.stl

Authored along +Z (crown up, skirt/clevis down), like the valve's poppet; the assembly
rotates it onto the cylinder's Y axis and slides it to the crank-angle position.
"""
import os
from build123d import *
from pump_params import BORE_D, WRIST_D, EPS, Pos, Rot

PISTON_CLEAR = 0.4
PISTON_D     = BORE_D - PISTON_CLEAR        # 15.6 slip fit in the Ø16 bore
PISTON_H     = 14.0

ORING_CS     = 2.0                          # O-ring cross-section; sits in a radial gland
GROOVE_Z     = 10.0                         # gland height up from the skirt
GROOVE_DEPTH = 1.4                          # radial groove depth (O-ring stands slightly proud)

CONROD_TH    = 6.0                          # connecting-rod small-end thickness
SLOT_W       = CONROD_TH + 0.4              # clevis slot (conrod swings in the Y-Z plane)
CLEVIS_DEPTH = 8.0                          # slot depth up from the skirt
WRIST_Z      = 4.0                          # wrist-pin height from the skirt


def part():
    p = Cylinder(PISTON_D / 2, PISTON_H, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # radial O-ring gland: subtract a torus so the groove is GROOVE_DEPTH deep (O-ring then
    # stands proud by ORING_CS - GROOVE_DEPTH to seal on the bore)
    gland = Pos(0, 0, GROOVE_Z) * Torus(PISTON_D / 2 - GROOVE_DEPTH + ORING_CS / 2, ORING_CS / 2)
    p = p.cut(gland)

    # rear clevis: a slot the conrod small-end sits in, + a cross wrist-pin bore
    slot = Box(SLOT_W, PISTON_D + 2 * EPS, CLEVIS_DEPTH,
               align=(Align.CENTER, Align.CENTER, Align.MIN))
    slot = Pos(0, 0, -EPS) * slot
    wrist = Pos(0, 0, WRIST_Z) * Rot(0, 90, 0) * Cylinder(WRIST_D / 2, PISTON_D + 2 * EPS)
    p = p.cut(slot, wrist)
    return p


# ---- mate points (local frame, piston axis = +Z) ------------------------------------
MATES = {
    "crown": Pos(0, 0, PISTON_H),           # front face (toward the port/plate)
    "wrist": Pos(0, 0, WRIST_Z),            # wrist-pin center (conrod small end)
}


if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    export_stl(part(), "build/piston.stl")
    import trimesh
    m = trimesh.load("build/piston.stl")
    print("piston:", (m.bounds[1] - m.bounds[0]).round(1),
          "bodies:", len(m.split(only_watertight=False)),
          "watertight:", m.is_watertight)
