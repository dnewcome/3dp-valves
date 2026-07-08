"""vpump_sim.py — MuJoCo timing bench for the VERTICAL rotary-distributor pump.

The horizontal bench (pump_sim.py) showed a plain swinging eccentric seals the discharging
port only ~41% of the cycle (sinusoidal, no dwell). This bench closes the loop: it plays the
REAL vertical-pump meshes through the crank kinematics from vpump_params.py and measures the
same "port coverage", showing the coaxial ROTARY DISTRIBUTOR gets the dwell for free -- the
discharging port stays connected to the output ~89% of the cycle, no cam profile to tune.

The rotor is keyed to the shaft (world azimuth = phi + ROTOR_PHASE); its ~160deg kidney is
over whichever port is discharging for most of that cylinder's stroke, breaking only in the
~20deg dead-band at each changeover (where piston velocity ~ 0).

Modes:
  (default) interactive viewer -- crank auto-rotates; watch the kidney track the ports
  --demo      headless: render a gif + write the coverage figure (rotary vs plain eccentric)
  --selftest  build + pose + assert finite + coverage checks, no window (CI-safe)
    python sim/vpump_sim.py [--demo|--selftest]
"""
import os
import sys

_MODE = "demo" if "--demo" in sys.argv else "selftest" if "--selftest" in sys.argv else "interactive"
os.environ.setdefault("MUJOCO_GL", "glfw" if _MODE == "interactive" else "osmesa")

import numpy as np
import mujoco
from math import radians, degrees, sin, cos

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cad"))
import vpump_params as V
import piston

MM = 0.001
BUILD = os.path.join(os.path.dirname(__file__), "..", "build")
HALF = V.KIDNEY_ARC / 2.0     # kidney half-arc: sealed while |kidney - port| <= HALF


# ======================================================================================
# Kinematics (from vpump_params) -- crank angle phi drives everything
# ======================================================================================
def kidney_to_discharging(phi_deg):
    """Angular distance [deg] from the kidney center to the currently-discharging port."""
    port_az = 0.0 if V.discharging_side(phi_deg) > 0 else 180.0
    return abs(((V.kidney_center_az(phi_deg) - port_az + 180) % 360) - 180)


# ======================================================================================
# MuJoCo model (real meshes; joints + frames from vpump_params)
# ======================================================================================
def make_xml():
    def m(v):
        return v * MM
    wz = piston.WRIST_Z
    return f"""
<mujoco model="vertical_svalve_pump">
  <compiler angle="degree" meshdir="{BUILD}" autolimits="true"/>
  <option timestep="0.002" gravity="0 0 0"/>
  <visual>
    <global offwidth="900" offheight="1200"/>
    <headlight ambient="0.45 0.45 0.45" diffuse="0.5 0.5 0.5"/>
  </visual>
  <asset>
    <mesh name="block"  file="v_block.stl"      scale="0.001 0.001 0.001"/>
    <mesh name="crank"  file="v_crankshaft.stl" scale="0.001 0.001 0.001"/>
    <mesh name="rotor"  file="v_rotor.stl"      scale="0.001 0.001 0.001"/>
    <mesh name="piston" file="piston.stl"       scale="0.001 0.001 0.001"/>
  </asset>
  <worldbody>
    <light pos="0.1 -0.2 0.3" dir="-0.3 0.6 -0.8"/>
    <geom name="block" type="mesh" mesh="block" rgba="0.80 0.80 0.83 0.20" contype="0" conaffinity="0"/>
    <geom name="riser" type="cylinder" size="{m(V.RISER_D/2)} {m((V.RISER_TOP-(V.ROTOR_Z0+V.ROTOR_H))/2)}"
          pos="0 0 {m((V.RISER_TOP+V.ROTOR_Z0+V.ROTOR_H)/2)}" rgba="0.27 0.45 0.62 1"
          contype="0" conaffinity="0"/>

    <body name="crank" pos="0 0 0">
      <joint name="crank" type="hinge" axis="0 0 1"/>
      <geom type="mesh" mesh="crank" rgba="0.34 0.34 0.38 1" contype="0" conaffinity="0"/>
      <site name="pin" pos="{m(V.THROW)} 0 {m(V.CYL_Z)}" size="0.0025" rgba="1 1 0 1"/>
    </body>

    <body name="rotor" pos="0 0 {m(V.ROTOR_Z0)}">
      <joint name="rotor" type="hinge" axis="0 0 1"/>
      <geom type="mesh" mesh="rotor" rgba="0.30 0.72 0.28 1" contype="0" conaffinity="0"/>
    </body>

    <body name="piston_p" pos="0 0 {m(V.CYL_Z)}">
      <joint name="pist_p" type="slide" axis="1 0 0"/>
      <geom type="mesh" mesh="piston" pos="{m(-wz)} 0 0" euler="0 90 0"
            rgba="0.90 0.55 0.15 1" contype="0" conaffinity="0"/>
      <site name="wrist_p" pos="0 0 0" size="0.0025" rgba="1 1 0 1"/>
    </body>
    <body name="piston_n" pos="0 0 {m(V.CYL_Z)}">
      <joint name="pist_n" type="slide" axis="1 0 0"/>
      <geom type="mesh" mesh="piston" pos="{m(wz)} 0 0" euler="0 -90 0"
            rgba="0.90 0.55 0.15 1" contype="0" conaffinity="0"/>
      <site name="wrist_n" pos="0 0 0" size="0.0025" rgba="1 1 0 1"/>
    </body>
  </worldbody>

  <tendon>
    <spatial name="conrod_p" width="0.0018" rgba="0.85 0.70 0.25 1">
      <site site="pin"/><site site="wrist_p"/></spatial>
    <spatial name="conrod_n" width="0.0018" rgba="0.85 0.70 0.25 1">
      <site site="pin"/><site site="wrist_n"/></spatial>
  </tendon>
</mujoco>"""


def _adr(model, jname):
    return model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, jname)]


class Bench:
    def __init__(self):
        self.model = mujoco.MjModel.from_xml_string(make_xml())
        self.data = mujoco.MjData(self.model)
        self.q = {j: _adr(self.model, j) for j in ("crank", "rotor", "pist_p", "pist_n")}

    def pose(self, phi_deg):
        d = self.data
        d.qpos[self.q["crank"]] = radians(phi_deg)
        d.qpos[self.q["rotor"]] = radians(phi_deg + V.ROTOR_PHASE)
        d.qpos[self.q["pist_p"]] = V.wrist_x(phi_deg, +1) * MM
        d.qpos[self.q["pist_n"]] = V.wrist_x(phi_deg, -1) * MM
        mujoco.mj_forward(self.model, self.data)


# ======================================================================================
# Modes
# ======================================================================================
def run_interactive():
    import time
    import mujoco.viewer
    b = Bench()
    print(f"interactive: rotary distributor sealed {V.sealed_fraction()*100:.0f}% of the cycle")
    with mujoco.viewer.launch_passive(b.model, b.data) as v:
        phi = 0.0
        v.cam.azimuth, v.cam.elevation, v.cam.distance = -68, -10, 0.205
        v.cam.lookat[:] = [0.0, 0.0, 0.035]
        while v.is_running():
            phi = (phi + 1.2) % 360.0
            b.pose(phi)
            v.sync()
            time.sleep(1 / 120)


def _frames(b, n=90):
    ren = mujoco.Renderer(b.model, 1000, 760)
    cam = mujoco.MjvCamera()
    cam.azimuth, cam.elevation, cam.distance = -68, -10, 0.205
    cam.lookat[:] = [0.0, 0.0, 0.035]
    out = []
    for k in range(n):
        b.pose(360.0 * k / n)
        ren.update_scene(b.data, cam)
        out.append(ren.render().copy())
    ren.close()
    return out


def run_demo():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import imageio.v2 as imageio

    b = Bench()
    print("masses (kg): " + ", ".join(
        f"{mujoco.mj_id2name(b.model, mujoco.mjtObj.mjOBJ_BODY, i)}={b.model.body_mass[i]*1e3:.1f}g"
        for i in range(1, b.model.nbody)))

    phis = np.arange(0, 360, 0.5)
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    yp = [V.wrist_x(f, +1) for f in phis]
    yn = [V.wrist_x(f, -1) for f in phis]
    ax[0].plot(phis, yp, label="+X piston", color="tab:orange")
    ax[0].plot(phis, yn, label="-X piston", color="tab:brown")
    for f in phis:
        c = "tab:orange" if V.discharging_side(f) > 0 else "tab:brown"
        ax[0].axvspan(f, f + 0.5, color=c, alpha=0.06)
    ax[0].set_ylabel("piston X [mm]"); ax[0].legend(loc="upper right", fontsize=8)
    ax[0].set_title("Vertical pump drive timing — shaded = that cylinder DISCHARGES")

    d = np.array([kidney_to_discharging(f) for f in phis])
    sealed = d <= HALF
    ax[1].plot(phis, d, color="tab:blue", lw=1.6, label="kidney → discharging-port angle")
    ax[1].axhline(HALF, color="k", ls="--", lw=1, label=f"kidney half-arc ({HALF:.0f}°)")
    ax[1].fill_between(phis, 0, 180, where=sealed, color="tab:green", alpha=0.12, label="CONNECTED to output")
    frac = V.sealed_fraction()
    ax[1].set_ylabel("angle [deg]"); ax[1].set_xlabel("crank angle phi [deg]")
    ax[1].set_title(f"ROTARY DISTRIBUTOR — discharging port connected {frac*100:.0f}% of the "
                    f"cycle (vs ~41% for a plain sinusoidal eccentric)")
    ax[1].legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(BUILD, "vpump_sim_timing.png"), dpi=110)
    plt.close(fig)
    print("wrote build/vpump_sim_timing.png")

    try:
        frames = _frames(b)
        imageio.mimsave(os.path.join(BUILD, "vpump_sim.gif"), frames, fps=24, loop=0)
        print("wrote build/vpump_sim.gif")
    except Exception as e:
        print("gif skipped:", type(e).__name__, e)


def selftest():
    b = Bench()
    for f in np.linspace(0, 360, 13):
        b.pose(float(f))
        assert np.all(np.isfinite(b.data.qpos)), f"non-finite qpos at phi={f}"
    # known geometry: at phi=270 the +X cylinder is mid-discharge and the kidney is dead on
    assert kidney_to_discharging(270.0) < 1e-6, "kidney should be exactly on the +X port at phi=270"
    # the point: the rotary distributor holds the dwell a plain eccentric can't
    frac = V.sealed_fraction()
    assert frac > 0.85, f"expected high coverage from the rotary valve, got {frac:.2f}"
    print(f"selftest OK: rotary distributor seals the discharging port {frac*100:.0f}% of the "
          f"cycle (kidney {V.KIDNEY_ARC:.0f}°); vs ~41% for a plain sinusoidal eccentric")


if __name__ == "__main__":
    {"interactive": run_interactive, "demo": run_demo, "selftest": selftest}[_MODE]()
