"""v_pump_assembly.py — the VERTICAL submersible S-valve pump, placed from vpump_params.
Writes:
  build/v_pump_assembly.stl          full assembly mesh
  build/v_pump_assembly_section.stl  Y=0 half-section (both cylinders + valve + riser)
  build/v_pump_assembly.png          colored exterior view (with waterline)
  build/v_pump_assembly_section.png  colored section (the vertical flow path)

Frozen at crank angle PHI (0): the +X cylinder is at front dead center (discharging), the
rotor kidney is over the +X port routing it up the riser, and the -X cylinder is retracted
(drawing from the bath). Conrods + the output riser are drawn as reference links.
"""
import os
import tempfile
import numpy as np
import trimesh
from build123d import export_stl
import vpump_params as V
from vpump_params import (CYL_Z, THROW, ROTOR_Z0, ROTOR_H, ROTOR_PHASE, RISER_D, RISER_TOP,
                          WATERLINE, wrist_x, discharging_side, kidney_center_az, port_sealed,
                          Pos, Rot)
import v_block
import v_crankshaft
import v_rotor
import piston
from math import radians, cos, sin

PHI = 300.0     # mid +X-discharge: piston well forward, kidney over the +X port

COLOR = {
    "v_block":      (0.78, 0.78, 0.81),
    "v_crankshaft": (0.34, 0.34, 0.38),
    "v_rotor":      (0.30, 0.72, 0.28),     # green = the distributor valve
    "piston":       (0.90, 0.55, 0.15),
    "conrod":       (0.85, 0.70, 0.25),
    "riser":        (0.27, 0.45, 0.62),
}
WETTED = {"v_block", "v_rotor", "piston"}


def _mesh(solid, name):
    f = tempfile.mktemp(suffix=".stl"); export_stl(solid, f)
    m = trimesh.load(f); os.remove(f)
    return (name, m, COLOR[name])


def _link(p0, p1, d, name):
    m = trimesh.creation.cylinder(radius=d / 2, segment=(np.array(p0), np.array(p1)))
    return (name, m, COLOR[name])


def pieces():
    out = [_mesh(v_block.part(), "v_block")]
    out.append(_mesh(v_crankshaft.part(PHI), "v_crankshaft"))
    out.append(_mesh(Pos(0, 0, ROTOR_Z0) * Rot(0, 0, PHI + ROTOR_PHASE) * v_rotor.part(), "v_rotor"))

    # opposed pistons: crown toward the outer port (+X for A, -X for B)
    for sx, ry in ((+1, 90), (-1, -90)):
        wx = wrist_x(PHI, sx)
        T = Pos(wx, 0, CYL_Z) * Rot(0, ry, 0) * Pos(0, 0, -piston.WRIST_Z)
        out.append(_mesh(T * piston.part(), "piston"))

    # conrods: shared crankpin -> each wrist
    px, py = THROW * cos(radians(PHI)), THROW * sin(radians(PHI))
    for sx in (+1, -1):
        out.append(_link((px, py, CYL_Z), (wrist_x(PHI, sx), 0, CYL_Z), 6.0, "conrod"))

    # output riser (up to the surface) from the rotor's central output
    out.append(_link((0, 0, ROTOR_Z0 + ROTOR_H - 1), (0, 0, RISER_TOP), RISER_D, "riser"))
    return out


def render(pcs, path, title, elev=14, azim=-72, waterline=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    light = np.array([0.4, -0.7, 0.55]); light /= np.linalg.norm(light)
    az, el = np.radians(azim), np.radians(elev)
    fwd = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    fig = plt.figure(figsize=(9, 10))
    ax = fig.add_subplot(111, projection="3d")
    allv = np.vstack([m.vertices for m, _ in pcs if len(m.vertices)])
    for m, rgb in sorted(pcs, key=lambda mc: -mc[0].centroid @ fwd):
        if not len(m.faces):
            continue
        shade = 0.4 + 0.6 * np.clip(m.face_normals @ light, 0, 1)
        cols = np.column_stack([rgb[0] * shade, rgb[1] * shade, rgb[2] * shade, np.ones_like(shade)])
        ax.add_collection3d(Poly3DCollection(m.vertices[m.faces], facecolors=cols, edgecolors="none"))
    b0, b1 = allv.min(0), allv.max(0)
    if waterline:
        xx, yy = np.meshgrid([b0[0], b1[0]], [b0[1], b1[1]])
        ax.plot_surface(xx, yy, np.full_like(xx, WATERLINE), color=(0.3, 0.5, 0.8), alpha=0.15)
        ax.text(b1[0], b0[1], WATERLINE, "  waterline", color=(0.2, 0.35, 0.6))
    ax.set_xlim(b0[0], b1[0]); ax.set_ylim(b0[1], b1[1]); ax.set_zlim(b0[2], b1[2])
    ax.set_box_aspect(b1 - b0)
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(title); ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z  (up)")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def main():
    os.makedirs("build", exist_ok=True)

    # timing proof: the rotor kidney sits over whichever port is discharging
    disch = discharging_side(PHI)
    port_az = 0.0 if disch > 0 else 180.0
    assert port_sealed(PHI, port_az), "rotor kidney is NOT over the discharging port!"
    print(f"OK valve timing: at phi={PHI:.0f} the {'+X' if disch>0 else '-X'} cylinder "
          f"discharges and the kidney (az {kidney_center_az(PHI):.0f}) covers its port")

    pcs = pieces()
    print("v-pump manifest:")
    for name, m, _ in pcs:
        print(f"  {name:14s} bbox {(m.bounds[1] - m.bounds[0]).round(1)}")

    full = trimesh.util.concatenate([m for _, m, _ in pcs])
    full.export("build/v_pump_assembly.stl")
    span = full.bounds[1] - full.bounds[0]
    print("assembly bbox:", span.round(1))
    assert span.max() < 300, "bbox exploded -> a part is mis-placed"

    # Y>=0 half-section over the wetted path (both cylinders, valve, riser all lie at y~0)
    sect = []
    for name, m, rgb in pcs:
        if name not in WETTED:
            continue
        h = m.slice_plane([0, 0, 0], [0, 1, 0], cap=True)
        if h is not None and len(h.faces):
            sect.append((h, rgb))
    trimesh.util.concatenate([m for m, _ in sect]).export("build/v_pump_assembly_section.stl")

    try:
        render([(m, c) for _, m, c in pcs], "build/v_pump_assembly.png",
               "Vertical submersible S-valve pump — exterior", elev=12, azim=-70, waterline=True)
        render(sect, "build/v_pump_assembly_section.png",
               "Vertical pump — Y>=0 section: opposed cylinders -> 90deg up -> rotary valve -> riser",
               elev=10, azim=-88)
        print("wrote build/v_pump_assembly.png, build/v_pump_assembly_section.png")
    except Exception as e:
        print("png render skipped:", type(e).__name__, e)


if __name__ == "__main__":
    main()
