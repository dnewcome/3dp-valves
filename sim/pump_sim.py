"""pump_sim.py — MuJoCo timing bench for the twin-cylinder S-valve pump.

The design question (PUMP_BRIEF's riskiest unknown): can ONE crankshaft rock the swing
S-tube so its mouth stays sealed on the *discharging* cylinder's port for that whole
stroke -- or does a plain eccentric give SINUSOIDAL swing that only lines up on the port
for an instant, leaking the rest of the stroke (i.e. you need DWELL)?

This is a kinematics/timing question, so the bench plays the REAL CAD meshes back through
the crank kinematics imported from cad/pump_params.py (SI: CAD mm * 0.001). Nothing is
re-modeled. The "felt quantity" is PORT COVERAGE -- the mouth-to-port misalignment vs
crank angle -- and the decisive comparison is a plain SINE eccentric vs a DWELL profile.

Modes (one file):
  (default) interactive viewer -- the crank auto-rotates; watch the mouth track the ports
  --demo      headless: render a gif + write the timing/coverage figure
  --selftest  build + pose + assert finite + known-geometry checks, no window (CI-safe)

NOTE ON DRIVE (a finding, not a bug): the crankshaft turns about X but the S-tube swings
about Y (perpendicular axes), so a single in-plane pushrod cannot couple them -- the swing
needs a right-angle take-off (bevel/crown gear to a pivot-coaxial crank, or a cam). This
bench therefore PRESCRIBES the swing profile to compare timing laws; picking the physical
mechanism that realizes the winning law is the follow-up.
    python sim/pump_sim.py [--demo|--selftest] [--dwell|--sine]
"""
import os
import sys

_MODE = "demo" if "--demo" in sys.argv else "selftest" if "--selftest" in sys.argv else "interactive"
os.environ.setdefault("MUJOCO_GL", "glfw" if _MODE == "interactive" else "osmesa")

import numpy as np
import mujoco
from math import radians, degrees, sin, cos, tanh, hypot

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cad"))
import pump_params as P          # single source of truth (same constants as the geometry)
import piston                    # WRIST_Z for the mesh transform

MM = 0.001
PROFILE = "dwell" if "--dwell" in sys.argv else "sine"
# The seal survives while the mouth center is within the ring's radial LAND of the port.
LAND = (P.RING_OD - P.PORT_D) / 2.0     # 2.5 mm here

BUILD = os.path.join(os.path.dirname(__file__), "..", "build")


# ======================================================================================
# Kinematics (all derived from pump_params) -- the crank angle phi drives everything
# ======================================================================================
def theta(phi_deg, profile=PROFILE):
    """S-tube swing angle [rad]. base=-sin(phi) puts the mouth on the +X port over the +X
    discharge window (phi in 180..360). SINE = plain eccentric (peaks on-port for an
    instant); DWELL = tanh-shaped near-square (parks on-port, flips fast at dead centers)."""
    A = radians(P.SWING_A)
    base = -sin(radians(phi_deg))
    if profile == "sine":
        return A * base
    return A * tanh(4.0 * base) / tanh(4.0)      # dwell, normalized so the peak == A


def mouth_xz(th):
    """Mouth center (x, z) [mm] on the wear plate for swing angle th."""
    return (P.MOUTH_R * sin(th), -P.ZPIVOT + P.MOUTH_R * cos(th))


def misalignment(phi_deg, profile=PROFILE):
    """Distance [mm] from the mouth to each port center (+X, -X)."""
    mx, mz = mouth_xz(theta(phi_deg, profile))
    return hypot(mx - P.PITCH / 2, mz), hypot(mx + P.PITCH / 2, mz)


def discharging_side(phi_deg):
    """+1 if the +X cylinder is discharging (piston moving toward the plate, +Y), else -1."""
    v = P.wrist_y(P.PHASE[+1] + phi_deg + 0.5) - P.wrist_y(P.PHASE[+1] + phi_deg - 0.5)
    return +1 if v > 0 else -1


def sealed_fraction(profile, n=720):
    """Fraction of the full cycle where the currently-discharging port is sealed
    (mouth within LAND of it). 1.0 = perfect valve timing."""
    ok = 0
    for k in range(n):
        phi = 360.0 * k / n
        d_plus, d_minus = misalignment(phi, profile)
        d_disch = d_plus if discharging_side(phi) > 0 else d_minus
        ok += (d_disch < LAND)
    return ok / n


# ======================================================================================
# MuJoCo model (real meshes, joints from params)
# ======================================================================================
def make_xml():
    def m(v):
        return v * MM
    return f"""
<mujoco model="s_valve_pump">
  <compiler angle="degree" meshdir="{BUILD}" autolimits="true"/>
  <option timestep="0.002" gravity="0 0 0"/>
  <visual>
    <global offwidth="1280" offheight="960"/>
    <headlight ambient="0.45 0.45 0.45" diffuse="0.5 0.5 0.5"/>
  </visual>
  <asset>
    <mesh name="block"  file="cylinder_block.stl" scale="0.001 0.001 0.001"/>
    <mesh name="crank"  file="crankshaft.stl"     scale="0.001 0.001 0.001"/>
    <mesh name="stube"  file="s_tube.stl"         scale="0.001 0.001 0.001"/>
    <mesh name="ring"   file="wear_ring.stl"      scale="0.001 0.001 0.001"/>
    <mesh name="piston" file="piston.stl"         scale="0.001 0.001 0.001"/>
  </asset>
  <worldbody>
    <light pos="0.1 -0.2 0.25" dir="-0.3 0.6 -0.7"/>
    <geom name="block" type="mesh" mesh="block" rgba="0.78 0.78 0.81 1"
          contype="0" conaffinity="0"/>

    <body name="crank" pos="0 {m(P.CRANK_Y)} 0">
      <joint name="crank" type="hinge" axis="1 0 0"/>
      <geom type="mesh" mesh="crank" rgba="0.34 0.34 0.38 1" contype="0" conaffinity="0"/>
      <site name="pin_p" pos="{m(P.PITCH/2)} {m(P.THROW)} 0" size="0.002" rgba="1 1 0 1"/>
      <site name="pin_n" pos="{m(-P.PITCH/2)} {m(-P.THROW)} 0" size="0.002" rgba="1 1 0 1"/>
    </body>

    <body name="stube" pos="0 0 {m(-P.ZPIVOT)}">
      <joint name="swing" type="hinge" axis="0 1 0"/>
      <geom type="mesh" mesh="stube" rgba="0.30 0.72 0.28 1" contype="0" conaffinity="0"/>
      <geom type="mesh" mesh="ring" pos="0 {m(P.MOUTH_Y)} {m(P.MOUTH_R)}" euler="90 0 0"
            rgba="0.82 0.20 0.20 1" contype="0" conaffinity="0"/>
    </body>

    <body name="piston_p" pos="{m(P.PITCH/2)} 0 0">
      <joint name="pist_p" type="slide" axis="0 1 0"/>
      <geom type="mesh" mesh="piston" pos="0 {m(-piston.WRIST_Z)} 0" euler="-90 0 0"
            rgba="0.90 0.55 0.15 1" contype="0" conaffinity="0"/>
      <site name="wrist_p" pos="0 0 0" size="0.002" rgba="1 1 0 1"/>
    </body>
    <body name="piston_n" pos="{m(-P.PITCH/2)} 0 0">
      <joint name="pist_n" type="slide" axis="0 1 0"/>
      <geom type="mesh" mesh="piston" pos="0 {m(-piston.WRIST_Z)} 0" euler="-90 0 0"
            rgba="0.90 0.55 0.15 1" contype="0" conaffinity="0"/>
      <site name="wrist_n" pos="0 0 0" size="0.002" rgba="1 1 0 1"/>
    </body>
  </worldbody>

  <tendon>
    <spatial name="conrod_p" width="0.0018" rgba="0.85 0.70 0.25 1">
      <site site="pin_p"/><site site="wrist_p"/></spatial>
    <spatial name="conrod_n" width="0.0018" rgba="0.85 0.70 0.25 1">
      <site site="pin_n"/><site site="wrist_n"/></spatial>
  </tendon>
</mujoco>"""


def _adr(model, jname):
    return model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, jname)]


class Bench:
    def __init__(self):
        self.model = mujoco.MjModel.from_xml_string(make_xml())
        self.data = mujoco.MjData(self.model)
        self.q = {j: _adr(self.model, j) for j in ("crank", "swing", "pist_p", "pist_n")}

    def pose(self, phi_deg, profile=PROFILE):
        d = self.data
        d.qpos[self.q["crank"]] = radians(phi_deg)
        d.qpos[self.q["swing"]] = theta(phi_deg, profile)
        d.qpos[self.q["pist_p"]] = P.wrist_y(P.PHASE[+1] + phi_deg) * MM
        d.qpos[self.q["pist_n"]] = P.wrist_y(P.PHASE[-1] + phi_deg) * MM
        mujoco.mj_forward(self.model, self.data)     # kinematic posing only (no integration)


# ======================================================================================
# Modes
# ======================================================================================
def run_interactive():
    import time
    import mujoco.viewer
    b = Bench()
    print(f"interactive: profile={PROFILE}  (crank auto-rotates; --dwell/--sine to switch)")
    with mujoco.viewer.launch_passive(b.model, b.data) as v:
        phi = 0.0
        v.cam.azimuth, v.cam.elevation, v.cam.distance = -68, -20, 0.205
        v.cam.lookat[:] = [0.0, -0.02, -0.012]
        while v.is_running():
            phi = (phi + 1.2) % 360.0
            b.pose(phi)
            v.sync()
            time.sleep(1 / 120)


def _frames(b, profile, n=90):
    ren = mujoco.Renderer(b.model, 720, 960)
    cam = mujoco.MjvCamera()
    cam.azimuth, cam.elevation, cam.distance = -68, -20, 0.205
    cam.lookat[:] = [0.0, -0.02, -0.012]
    out = []
    for k in range(n):
        b.pose(360.0 * k / n, profile)
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
    print(f"masses (kg): " + ", ".join(
        f"{mujoco.mj_id2name(b.model, mujoco.mjtObj.mjOBJ_BODY, i)}={b.model.body_mass[i]*1e3:.1f}g"
        for i in range(1, b.model.nbody)))

    phis = np.arange(0, 360, 0.5)
    fig, ax = plt.subplots(3, 1, figsize=(10, 9), sharex=True)

    # 1) pistons + discharge windows
    yp = [P.wrist_y(P.PHASE[+1] + f) for f in phis]
    yn = [P.wrist_y(P.PHASE[-1] + f) for f in phis]
    ax[0].plot(phis, yp, label="+X piston (wrist Y)", color="tab:orange")
    ax[0].plot(phis, yn, label="-X piston (wrist Y)", color="tab:brown")
    for f in phis:
        if discharging_side(f) > 0:
            ax[0].axvspan(f, f + 0.5, color="tab:orange", alpha=0.06)
        else:
            ax[0].axvspan(f, f + 0.5, color="tab:brown", alpha=0.06)
    ax[0].set_ylabel("piston Y [mm]"); ax[0].legend(loc="upper right", fontsize=8)
    ax[0].set_title("Drive timing — shaded = that cylinder is DISCHARGING (moving toward the plate)")

    # 2) & 3) misalignment of the mouth from the DISCHARGING port, per profile
    for row, profile in ((1, "sine"), (2, "dwell")):
        d_disch = []
        for f in phis:
            d_plus, d_minus = misalignment(f, profile)
            d_disch.append(d_plus if discharging_side(f) > 0 else d_minus)
        d_disch = np.array(d_disch)
        sealed = d_disch < LAND
        ax[row].plot(phis, d_disch, color="tab:blue", lw=1.6,
                     label="mouth→discharging-port misalignment")
        ax[row].axhline(LAND, color="k", ls="--", lw=1, label=f"seal limit (LAND={LAND:.1f}mm)")
        ax[row].fill_between(phis, 0, d_disch.max() * 1.05, where=sealed,
                             color="tab:green", alpha=0.12, label="SEALED")
        frac = sealed_fraction(profile)
        ax[row].set_ylabel("misalign [mm]")
        ax[row].set_title(f"{profile.upper()} swing — discharging port sealed "
                          f"{frac*100:.0f}% of the cycle")
        ax[row].legend(loc="upper right", fontsize=8)
    ax[2].set_xlabel("crank angle phi [deg]")
    fig.tight_layout()
    fig.savefig(os.path.join(BUILD, "pump_sim_timing.png"), dpi=110)
    plt.close(fig)
    print("wrote build/pump_sim_timing.png")

    try:
        frames = _frames(b, PROFILE)
        imageio.mimsave(os.path.join(BUILD, "pump_sim.gif"), frames, fps=24, loop=0)
        print(f"wrote build/pump_sim.gif ({PROFILE})")
    except Exception as e:
        print("gif skipped:", type(e).__name__, e)


def selftest():
    b = Bench()
    for f in np.linspace(0, 360, 13):
        b.pose(float(f))
        assert np.all(np.isfinite(b.data.qpos)), f"non-finite qpos at phi={f}"
    # known geometry: SINE mouth lands exactly on the +X port at phi=270 (peak of the swing)
    d_plus, _ = misalignment(270.0, "sine")
    assert d_plus < 1e-6, f"sine peak should hit +X port, got {d_plus:.3f}mm"
    # the whole point: dwell seals a much larger fraction than a plain sine eccentric
    fs, fd = sealed_fraction("sine"), sealed_fraction("dwell")
    assert fd > fs + 0.15, f"expected dwell >> sine, got sine={fs:.2f} dwell={fd:.2f}"
    print(f"selftest OK: sealed fraction  sine={fs*100:.0f}%  dwell={fd*100:.0f}%  "
          f"(LAND={LAND:.1f}mm, swing +/-{P.SWING_A:.1f}deg)")


if __name__ == "__main__":
    {"interactive": run_interactive, "demo": run_demo, "selftest": selftest}[_MODE]()
