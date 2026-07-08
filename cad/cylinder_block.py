"""cylinder_block.py — twin-cylinder body with the front WEAR PLATE.
Two parallel cylinder bores run along Y (pistons reciprocate in +/-Y), side by side in
X, both centered at z=0. The front PLATE_T slab (at y=0) is the wear plate: each bore
necks down to a Ø PORT_D port through it, giving a flat sealing LAND for the S-tube's
wear ring. The narrowed port (16 -> 12) is still 4x the design bead, so nothing clogs.
    python cad/cylinder_block.py -> build/cylinder_block.stl

Behind the plate the bores are open (pistons + conrods enter from the back). In front of
the plate (+Y) sits the hopper; a port not currently covered by the swing tube draws
slurry from that hopper as its piston retracts.
"""
import os
from build123d import *
from pump_params import (BLOCK_X, BLOCK_Z, CYL_LEN, PLATE_T, BORE_D, PORT_D,
                         PITCH, EPS, Pos, Rot)

L = CYL_LEN + PLATE_T                 # total block depth in Y (front face at y=0)


def _ycyl(d, y0, y1, x=0.0, z=0.0):
    """Cylinder with its axis along Y, spanning y0..y1."""
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(d / 2, y1 - y0)


def part():
    # block: front face at y=0, extends back to y=-L; cylinders centered on z=0
    body = Box(BLOCK_X, L, BLOCK_Z, align=(Align.CENTER, Align.MAX, Align.CENTER))

    cuts = []
    for sx in (-1, 1):
        x = sx * PITCH / 2
        # cylinder bore: open at the back, stops PLATE_T short of the front (leaves the plate)
        cuts.append(_ycyl(BORE_D, -L - EPS, -PLATE_T, x=x))
        # port: bore -> front face through the plate (bead-safe Ø PORT_D)
        cuts.append(_ycyl(PORT_D, -PLATE_T - EPS, EPS, x=x))

    body = body.cut(*cuts)
    return body


# ---- mate points (local frame; ports on the plate face, bores open at the back) ------
MATES = {
    "port_pos":  Pos(+PITCH / 2, 0, 0),      # +X cylinder port on the plate (y=0)
    "port_neg":  Pos(-PITCH / 2, 0, 0),      # -X cylinder port on the plate
    "bore_pos":  Pos(+PITCH / 2, -L, 0),     # +X bore mouth at the back (piston enters +Y)
    "bore_neg":  Pos(-PITCH / 2, -L, 0),     # -X bore mouth at the back
}


if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    export_stl(part(), "build/cylinder_block.stl")
    import trimesh
    m = trimesh.load("build/cylinder_block.stl")
    print("cylinder_block:", (m.bounds[1] - m.bounds[0]).round(1),
          "bodies:", len(m.split(only_watertight=False)),
          "watertight:", m.is_watertight)
