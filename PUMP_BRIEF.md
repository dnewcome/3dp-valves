# 3dp-pump — kickoff brief

A **solids-handling pump** subsystem for the 3dp-valves repo. Where the valve blocks
are all *small* precision orifices + poppet seats, the pump is the opposite: **large,
clear, unobstructed passages** so suspended solids never hit anything smaller than
themselves.

- **Problem:** Pump glass reflective beads suspended in **mineral oil** for an art
  project, with **zero clogging** — no bead-wetted passage or valve may ever narrow
  below the largest bead.
- **Done looks like:** One motor turns; two printed cylinders reciprocate 180° out of
  phase; a swinging **S-tube** valve alternately connects each cylinder to the outlet;
  bead-laden mineral oil moves continuously across the bench and **never jams**.
- **Not now:** High pressure/head, self-priming from a deep source, long-life / wear
  rating, and any flame-FX or existing-solenoid-valve integration. Bench scale,
  near-zero back-pressure.
- **First slice:** A parametric **twin-cylinder S-valve pump core** in build123d — two
  cylinder bores, the swing **S-tube**, and the **wear-plate + replaceable TPU
  wear-ring** sealing face — sized so every bead-wetted passage stays well above the
  largest bead, exporting clean watertight STLs. The pump analog of
  `solenoid_block.py` + `poppet.py`, reusing this repo's flat-TPU-seal trick.
- **Open question (riskiest):** The **swing-tube-to-wear-plate seal** on a *printed*
  part — can a pressure/spring-loaded TPU wear ring seal oil against a printed plate
  while beads sweep across it, and can a **single crankshaft** rock the S-tube in sync
  with the pistons (cam or second throw) rather than a separate actuator? Sim-able
  first with the repo's MuJoCo skill.
  - **Update (simulated, `sim/pump_sim.py`):** a plain eccentric gives *sinusoidal*
    swing that seals the discharging port only ~41 % of the cycle; a **dwell** profile
    gets ~82 %. And the swing axis (Y) is perpendicular to the crank axis (X), so the
    swing needs a **right-angle take-off + dwell cam**, not a plain pushrod. See
    [`PUMP.md`](PUMP.md) → *Drive timing*. Seal-against-abrasion is still open (bench test).

## Why the S-valve (swing tube), not a poppet/ball check

Concrete pumps move fluid full of rocks because the only "valve" is a **fat tube whose
bore is bigger than any rock**. The tube's outlet end is a fixed pivot at the discharge;
its inlet mouth swings across a **wear plate** with two kidney ports (one per cylinder),
connecting exactly one cylinder to the outlet while the other draws from the hopper. The
mouth seals against the plate via a **wear ring** loaded by discharge pressure —
self-sealing, but self-wearing (the caption "…that maybe seems like a great idea, but…").
Mineral oil is a *friendly* carrier here: viscous (keeps beads suspended, fills printed
clearances) and lubricating (glass-in-oil grinds the seal far less than glass dry/in
water).

## Key decisions locked
- **Architecture:** twin-piston + **S-tube swing valve** (positive displacement, large
  clear passages, near-continuous output).
- **Drive:** **single motor + crankshaft** — one shaft reciprocates both pistons 180°
  out of phase *and* rocks the S-tube in time (cam or second throw), so one motor runs
  everything.
- **Carrier / solids:** glass reflective beads in mineral oil, bench scale, low head.
- **Seal:** replaceable **TPU wear ring** on the swinging mouth against a printed wear
  plate (reuses the repo's TPU-seal material + method).
- **Materials check (before soaking):** confirm mineral-oil compatibility of the chosen
  print resin/filament (PETG, TPU, cured SLA are generally fine).
