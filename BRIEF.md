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
- **Open question (riskiest):** Coil pull vs. pressure on OPEN. With pressure-to-close
  (below), the spring is trivial but the solenoid must lift the poppet against
  P × orifice-area + spring. This caps the openable orifice: A_max ≈ F_coil / P.
  For a ~6 N coil (minus ~1 N spring): Ø6 at 25 psi (huge margin), but only ~Ø3 at
  100 psi. So Ø3 is comfortable for propane and right at the limit for 100 psi air —
  bigger pneumatic flow needs a bigger coil or a pilot/3-way (the A/B+exhaust stretch).

## Key decisions locked
- **Actuation:** Custom poppet + coil (fully parametric; we own sealing/force/spring).
- **Force orientation: PRESSURE-TO-CLOSE.** Supply fills the chamber and presses the
  poppet onto the seat, so pressure helps seal and the return spring is a light
  reseat-only spring (~0.5–1 N). The solenoid opens from the seated position, where
  the magnetic gap is smallest and coil force is greatest. (Beats pressure-to-open,
  where the spring is weakest exactly when it must hold against full pressure.)
- **Process:** SLA printing (good surface finish for seat/poppet sealing).
- **Pressures:** 25 psi propane (primary), 100 psi air/pneumatics (stretch).
- **Fallback under evaluation:** COTS miniature solenoid valves if custom poppet
  sealing proves unreliable.
