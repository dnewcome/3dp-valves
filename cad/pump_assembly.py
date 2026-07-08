"""pump_assembly.py — the twin-cylinder S-valve pump, placed BY the shared params +
kinematics (nothing hand-tuned) and rendered. Writes:
  build/pump_assembly.stl          full assembly mesh
  build/pump_assembly_section.stl  X>=0 half-section (one full channel: piston->port->tube)
  build/pump_assembly.png          colored exterior view
  build/pump_assembly_section.png  colored section view

Frozen at crank angle PHI (default 0): the +X piston is at front dead center (discharging)
and the S-tube is swung onto the +X port; the -X piston sits at back dead center, its port
open to the hopper. Connecting rods + the swing pushrod are drawn as straight links between
the pin centers the crankshaft defines (schematic; exact swing timing is a MuJoCo job).
"""
import os
import tempfile
import numpy as np
import trimesh
from math import radians, sin, cos

from build123d import export_stl
from pump_params import (SWING_A, ZPIVOT, PITCH, PHASE, CRANK_Y, X_SWING, SWING_ARM,
                         SWING_DRIVE_PHASE, MOUTH_Y, crank_offset, swing_offset, wrist_y,
                         Pos, Rot)
import cylinder_block
import s_tube
import wear_ring
import piston
import crankshaft

PHI   = 0.0        # crank angle for this render
THETA = SWING_A    # S-tube swing angle (+ = onto the +X port, the discharging side)

COLOR = {
    "cylinder_block": (0.78, 0.78, 0.81),   # light gray
    "s_tube":         (0.30, 0.72, 0.28),   # green (the swing tube, like the reference video)
    "wear_ring":      (0.82, 0.20, 0.20),   # red (TPU seal)
    "piston":         (0.90, 0.55, 0.15),   # orange
    "crankshaft":     (0.34, 0.34, 0.38),   # dim gray
    "conrod":         (0.85, 0.70, 0.25),   # gold
    "swing":          (0.55, 0.35, 0.72),   # purple (swing arm + pushrod)
}


WETTED = {"cylinder_block", "s_tube", "wear_ring", "piston"}   # bead-touching parts (the section)


def _mesh(solid, name):
    """Export a placed build123d solid and load it as a named, colored trimesh."""
    f = tempfile.mktemp(suffix=".stl")
    export_stl(solid, f)
    m = trimesh.load(f)
    os.remove(f)
    return (name, m, COLOR[name])


def _link(p0, p1, d, name):
    """A straight rod (reference linkage) between two world points."""
    m = trimesh.creation.cylinder(radius=d / 2, segment=(np.array(p0), np.array(p1)))
    return (name, m, COLOR[name])


def pieces():
    out = []
    Tt = Pos(0, 0, -ZPIVOT) * Rot(0, THETA, 0)          # S-tube swing transform (about the pivot)

    out.append(_mesh(cylinder_block.part(), "cylinder_block"))
    out.append(_mesh(Tt * s_tube.part(), "s_tube"))
    out.append(_mesh(Tt * wear_ring.at_mouth(), "wear_ring"))
    out.append(_mesh(Pos(0, CRANK_Y, 0) * crankshaft.part(PHI), "crankshaft"))

    # pistons: placed by the crank kinematics (wrist Y from conrod angularity)
    for sx in (-1, 1):
        wy = wrist_y(PHASE[sx] + PHI)
        Tp = Pos(sx * PITCH / 2, wy, 0) * Rot(-90, 0, 0) * Pos(0, 0, -piston.WRIST_Z)
        out.append(_mesh(Tp * piston.part(), "piston"))

    # connecting rods: crankpin (big end) -> wrist (small end)
    for sx in (-1, 1):
        dy, dz = crank_offset(PHASE[sx] + PHI)
        big   = (sx * PITCH / 2, CRANK_Y + dy, dz)
        small = (sx * PITCH / 2, wrist_y(PHASE[sx] + PHI), 0.0)
        out.append(_link(big, small, piston.CONROD_TH, "conrod"))

    # swing drive: eccentric pin -> (pushrod) -> arm end -> (arm) -> pivot
    sdy, sdz = swing_offset(SWING_DRIVE_PHASE + PHI)
    spin  = (X_SWING, CRANK_Y + sdy, sdz)
    pivot = (0.0, 0.0, -ZPIVOT)
    arm_end = (-SWING_ARM * sin(radians(THETA)), 0.0, -ZPIVOT - SWING_ARM * cos(radians(THETA)))
    out.append(_link(pivot, arm_end, 6.0, "swing"))      # swing arm (lever on the pivot)
    out.append(_link(arm_end, spin, 4.0, "swing"))       # swing pushrod to the crank eccentric
    return out


def render(pcs, path, title, elev=20, azim=-60):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    light = np.array([0.4, -0.7, 0.55]); light = light / np.linalg.norm(light)
    az, el = np.radians(azim), np.radians(elev)
    fwd = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")
    allv = np.vstack([m.vertices for m, _ in pcs if len(m.vertices)])
    for m, rgb in sorted(pcs, key=lambda mc: -mc[0].centroid @ fwd):   # far -> near (painter)
        if not len(m.faces):
            continue
        shade = 0.4 + 0.6 * np.clip(m.face_normals @ light, 0, 1)
        cols = np.column_stack([rgb[0] * shade, rgb[1] * shade, rgb[2] * shade,
                                np.ones_like(shade)])
        ax.add_collection3d(Poly3DCollection(m.vertices[m.faces], facecolors=cols,
                                             edgecolors="none"))
    b0, b1 = allv.min(0), allv.max(0)
    ax.set_xlim(b0[0], b1[0]); ax.set_ylim(b0[1], b1[1]); ax.set_zlim(b0[2], b1[2])
    ax.set_box_aspect(b1 - b0)
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(title); ax.set_xlabel("x"); ax.set_ylabel("y  (discharge +)"); ax.set_zlabel("z")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def main():
    os.makedirs("build", exist_ok=True)

    # geometry proof: the swung S-tube mouth must land on the +X port (same X,Z; offset in Y
    # by exactly the wear-ring gap). If this holds, the whole swing kinematic is sound.
    Tt = Pos(0, 0, -ZPIVOT) * Rot(0, THETA, 0)
    mouth = (Tt * s_tube.MATES["mouth"]).position
    port = cylinder_block.MATES["port_pos"].position
    assert abs(mouth.X - port.X) < 1e-6 and abs(mouth.Z - port.Z) < 1e-6, \
        f"mouth {tuple(round(v,3) for v in mouth)} misses port {tuple(port)}"
    assert abs(mouth.Y - (port.Y + MOUTH_Y)) < 1e-6, "mouth->plate gap != wear-ring thickness"
    print(f"OK swing check: mouth lands on +X port at x={mouth.X:.1f} z={mouth.Z:.1f}, "
          f"gap {mouth.Y - port.Y:.1f}mm == ring")

    pcs = pieces()
    print("pump assembly manifest:")
    for name, m, _ in pcs:
        print(f"  {name:16s} bbox {(m.bounds[1] - m.bounds[0]).round(1)}")

    full = trimesh.util.concatenate([m for _, m, _ in pcs])
    full.export("build/pump_assembly.stl")
    span = (full.bounds[1] - full.bounds[0])
    print("assembly bbox:", span.round(1))
    assert span.max() < 300, "bbox exploded -> a part is mis-placed"

    # X>=0 half-section over the WETTED path only (piston -> bore -> port -> tube -> discharge);
    # the drive train stays in the exterior view so the flow path reads cleanly. slice_plane
    # (capped) tolerates the swept-tube mesh, which the strict boolean engine rejects.
    sect = []
    for name, m, rgb in pcs:
        if name not in WETTED:
            continue
        h = m.slice_plane([0, 0, 0], [1, 0, 0], cap=True)    # keep x >= 0
        if h is not None and len(h.faces):
            sect.append((h, rgb))
    trimesh.util.concatenate([m for m, _ in sect]).export("build/pump_assembly_section.stl")

    try:
        render([(m, c) for _, m, c in pcs], "build/pump_assembly.png",
               "Twin-cylinder S-valve pump — exterior (crank phi=0, +X discharging)")
        render(sect, "build/pump_assembly_section.png",
               "S-valve pump — X>=0 section: piston -> port -> swing tube -> discharge",
               elev=16, azim=-158)
        print("wrote build/pump_assembly.png, build/pump_assembly_section.png")
    except Exception as e:
        print("png render skipped:", type(e).__name__, e)


if __name__ == "__main__":
    main()
