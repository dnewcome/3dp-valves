"""interface.py — the standard mating-face PORT INTERFACE shared by all blocks.
This is the heart of the composable manifold system: any two blocks that share this
interface (port + gasket groove + bolt pattern) can bolt together with a TPU face
gasket sealing the joint. Change a value here and every block re-fits on rebuild.

Convention: blocks have a square TILE footprint and bolt together face-to-face.
The gasket GROOVE lives on one face (the manifold); the mating face is flat (land).
"""

TILE          = 30.0    # standard square block footprint (x, y)
PORT_D        = 4.0     # through-port diameter at the interface

BOLT_CLEAR_D  = 3.4     # M3 clearance (passes through the upper block)
BOLT_INSERT_D = 4.0     # M3 heat-set insert bore (in the lower/manifold block); through-bore
BOLT_INSET    = 4.5     # bolt inset from each tile edge

GASKET_CL_D   = 9.0     # gasket groove centerline diameter (around the port)
GASKET_W      = 2.0     # gasket groove width
GASKET_DEPTH  = 1.0     # gasket groove depth (TPU gasket sits here, protrudes to seal)


def bolt_xy(cx=0.0, cy=0.0):
    """Corner bolt positions for a tile centered at (cx, cy)."""
    h = TILE / 2 - BOLT_INSET
    return [(cx + sx * h, cy + sy * h) for sx in (-1, 1) for sy in (-1, 1)]
