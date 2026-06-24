# Flame-FX gas/pneumatic manifold — kickoff brief

- **Problem:** Sophisticated flame effects (and pneumatic cylinder control) normally
  need lots of expensive miniature gas valves + manifolds. Build a cheap, SLA-printed,
  parametric alternative where flow schematics become composable solid-modeled blocks.
- **Done looks like:** One printed inlet manifold block feeding **2 custom solenoid
  blocks**, each with a coil + ferrous plunger seating a TPU poppet against a printed
  seat, switching independent outputs on/off — holding 25 psi propane (target) /
  100 psi air (stretch).
- **Not now:** Gas-tightness of printed *walls* (SLA handles it); the A/B + exhaust
  2-way cylinder valve (stretch); full schematic→geometry compiler; flame-effect
  choreography / control electronics.
- **First slice:** A **single parametric solenoid block** in build123d — inlet/outlet
  ports, valve seat + orifice, TPU poppet groove, plunger guide bore, and coil bore —
  sized around one specific off-the-shelf coil + plunger, exporting a clean watertight
  STL. Get *one channel* sealing before manifolding two.
- **Open question (riskiest):** Force balance — can a small direct-acting coil's
  plunger force hold the poppet shut against pressure across the orifice
  (F ≈ P × orifice area), with a return spring, while still being printable?
  At 100 psi a 3 mm orifice needs ~1 lbf of seating force; orifice diameter, spring
  rate, and coil pull are coupled. May force a small orifice or a pilot-assisted design.

## Key decisions locked
- **Actuation:** Custom poppet + coil (fully parametric; we own sealing/force/spring).
- **Process:** SLA printing (good surface finish for seat/poppet sealing).
- **Pressures:** 25 psi propane (primary), 100 psi air/pneumatics (stretch).
- **Fallback under evaluation:** COTS miniature solenoid valves if custom poppet
  sealing proves unreliable.
