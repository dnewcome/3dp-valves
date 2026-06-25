"""assembly.py — positions all parts (including the reference solenoid) into the
2-channel valve stack and writes:
  build/assembly.stl          full assembly mesh
  build/assembly_section.stl  Y=0 half-section (reveals the on-axis flow path)
  build/assembly.png          colored exterior view
  build/assembly_section.png  colored section view
so you can see how everything fits. Run the part + solenoid builds first.
"""
import os
import numpy as np
import trimesh

from manifold import MAN_H, PITCH
from solenoid_block import SEAT_FLOOR_Z, SEAT_RAISE  # =12, 1 -> land top z=13

B = "build"
SEAT_TOP = SEAT_FLOOR_Z + SEAT_RAISE          # 13 (local block z where the disc seats)

# part -> base color (RGB). Distinct hues so each piece reads in the render.
COLOR = {
    "manifold":         (0.27, 0.45, 0.62),   # steel blue
    "solenoid_block":   (0.78, 0.78, 0.81),   # light gray
    "poppet":           (0.90, 0.55, 0.15),   # orange
    "tpu_disc":         (0.82, 0.20, 0.20),   # red
    "solenoid_coil":    (0.34, 0.34, 0.38),   # dim gray
    "solenoid_plunger": (0.85, 0.70, 0.25),   # gold
}


def placed(name, x, y, z):
    m = trimesh.load(os.path.join(B, f"{name}.stl"))
    m.apply_translation([x, y, z])
    return m, COLOR[name]


def render(pieces, path, title, elev=18, azim=-72):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    light = np.array([0.3, -0.7, 0.6]); light = light / np.linalg.norm(light)
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")

    allv = np.vstack([m.vertices for m, _ in pieces])
    for m, rgb in pieces:
        if not len(m.faces):
            continue
        shade = 0.4 + 0.6 * np.clip(m.face_normals @ light, 0, 1)
        cols = np.column_stack([rgb[0] * shade, rgb[1] * shade, rgb[2] * shade,
                                np.ones_like(shade)])
        ax.add_collection3d(Poly3DCollection(m.vertices[m.faces], facecolors=cols,
                                             edgecolors="none"))
    b0, b1 = allv.min(0), allv.max(0)
    ax.set_xlim(b0[0], b1[0]); ax.set_ylim(b0[1] - 15, b1[1] + 15); ax.set_zlim(b0[2], b1[2])
    ax.set_box_aspect((b1 - b0 + [0, 30, 0]))
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(title); ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def main():
    pieces = [placed("manifold", 0, 0, 0)]
    for cx in (-PITCH / 2, PITCH / 2):
        pieces.append(placed("solenoid_block", cx, 0, MAN_H))
        pieces.append(placed("poppet", cx, 0, MAN_H + SEAT_TOP + 0.4))   # 0.4 = disc protrusion
        pieces.append(placed("tpu_disc", cx, 0, MAN_H + SEAT_TOP))
        pieces.append(placed("solenoid_coil", cx, 0, MAN_H))
        pieces.append(placed("solenoid_plunger", cx, 0, MAN_H))

    full = trimesh.util.concatenate([m for m, _ in pieces])
    full.export(os.path.join(B, "assembly.stl"))

    # Y=0 section via boolean half-space (manifold3d; avoids slice_plane's deps).
    # Keep the y>=0 half so the cut face (normal -y) faces the default camera.
    cutter = trimesh.creation.box(extents=[400, 400, 400])
    cutter.apply_translation([0, 200, 0])           # occupies y in [0, 400]
    sect_pieces = []
    for m, rgb in pieces:
        h = trimesh.boolean.intersection([m, cutter], engine="manifold")
        if h is not None and len(h.faces):
            sect_pieces.append((h, rgb))
    section = trimesh.util.concatenate([m for m, _ in sect_pieces])
    section.export(os.path.join(B, "assembly_section.stl"))

    print("assembly:", full.bounds[1].round(1), "section bodies:",
          len(section.split(only_watertight=False)))

    try:
        render(pieces, os.path.join(B, "assembly.png"),
               "2-channel valve stack — exterior")
        render(sect_pieces, os.path.join(B, "assembly_section.png"),
               "2-channel valve stack — Y=0 section (flow path + solenoid on axis)",
               elev=8, azim=-88)
        print("wrote build/assembly.png, build/assembly_section.png")
    except Exception as e:
        print("png render skipped:", type(e).__name__, e)


if __name__ == "__main__":
    main()
