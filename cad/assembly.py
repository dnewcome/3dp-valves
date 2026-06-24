"""assembly.py — positions the built parts into the 2-channel valve stack and writes
a full assembly STL plus a Y=0 SECTION STL (and a PNG if an offscreen GL context is
available) so the internal flow path / stack-up can be eyeballed before printing.
    python cad/assembly.py -> build/assembly.stl, build/assembly_section.stl[, .png]

Run the part builds first (they populate build/*.stl).
"""
import os
import numpy as np
import trimesh

from manifold import MAN_H, PITCH
from solenoid_block import SEAT_FLOOR_Z, SEAT_RAISE  # =12, 1 -> land top z=13

B = "build"
SEAT_TOP = SEAT_FLOOR_Z + SEAT_RAISE          # 13 (local block z where the disc seats)


def placed(name, x, y, z):
    m = trimesh.load(os.path.join(B, f"{name}.stl"))
    m.apply_translation([x, y, z])
    return m


def main():
    parts = []
    parts.append(placed("manifold", 0, 0, 0))
    for cx in (-PITCH / 2, PITCH / 2):
        parts.append(placed("solenoid_block", cx, 0, MAN_H))
        parts.append(placed("poppet", cx, 0, MAN_H + SEAT_TOP + 0.4))   # 0.4 = disc protrusion
        parts.append(placed("tpu_disc", cx, 0, MAN_H + SEAT_TOP))

    full = trimesh.util.concatenate(parts)
    full.export(os.path.join(B, "assembly.stl"))

    # Y=0 section: intersect with a half-space box (y<=0) to reveal the on-axis flow
    # path. Boolean via manifold3d avoids the shapely/networkx slice_plane deps.
    cutter = trimesh.creation.box(extents=[400, 400, 400])
    cutter.apply_translation([0, -200, 0])          # occupies y in [-400, 0]
    halves = []
    for p in parts:
        h = trimesh.boolean.intersection([p, cutter], engine="manifold")
        if h is not None and len(h.faces):
            halves.append(h)
    section = trimesh.util.concatenate(halves)
    section.export(os.path.join(B, "assembly_section.stl"))

    print("assembly:", full.bounds[1].round(1), "section bodies:",
          len(section.split(only_watertight=False)))

    # PNG via matplotlib (headless, no GL needed) — render the section triangles
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        fig = plt.figure(figsize=(11, 8))
        ax = fig.add_subplot(111, projection="3d")
        tris = section.vertices[section.faces]
        # simple lambert shading from face normals
        n = section.face_normals
        light = np.array([0.3, -0.7, 0.6]); light = light / np.linalg.norm(light)
        shade = 0.35 + 0.65 * np.clip(n @ light, 0, 1)
        colors = np.column_stack([0.55 * shade, 0.62 * shade, 0.72 * shade,
                                  np.ones_like(shade)])
        pc = Poly3DCollection(tris, facecolors=colors, edgecolors="none")
        ax.add_collection3d(pc)
        b0, b1 = section.bounds
        ax.set_xlim(b0[0], b1[0]); ax.set_ylim(b0[1] - 20, b1[1] + 20)
        ax.set_zlim(b0[2], b1[2]); ax.set_box_aspect((b1 - b0 + [0, 40, 0]))
        ax.view_init(elev=18, azim=-72)
        ax.set_title("2-channel valve stack — Y=0 section (flow path on axis)")
        ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
        fig.tight_layout()
        fig.savefig(os.path.join(B, "assembly_section.png"), dpi=110)
        print("wrote build/assembly_section.png")
    except Exception as e:
        print("png render skipped:", type(e).__name__, e)


if __name__ == "__main__":
    main()
