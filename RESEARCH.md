# Solenoid & valve research

Research backing the actuation decisions in [BRIEF.md](BRIEF.md). Two paths:
the **custom poppet** (chosen) and a **COTS fallback** to de-risk sealing.

## Custom-poppet path — bare solenoids to design around

| Solenoid | Force / stroke | Duty | Notes |
|---|---|---|---|
| **Makermotor PN00121** (12V tubular push-pull) | 6N @ 10mm, 1.85A | continuous (listed) | Cheap (~$15–20), defined spec sheet — primary part to design around |
| **Generic 8mm-plunger push-pull** (Amazon/AliExpress) | 2–15N, 2–20mm stroke, 7–25W | continuous variants exist | Cheapest; specs vary by listing — buy & measure |
| **Murphy RP2307B / RP2309B** | 49–62N pull, 102–151N hold | continuous | Large/overkill, but shows pattern: hold force >> pull force |

**Key physics:** solenoid force is highest at end-of-stroke (smallest air gap).
A poppet seats at end-of-stroke — exactly where the coil is strongest. Design the
geometry so the magnetic gap is smallest at the sealed position. 100 psi × 3 mm
orifice ≈ 4.5 N seating force; the small 6 N unit clears it *if near-seated*.

## COTS fallback — drop-in valves if custom sealing flunks

**Propane / 25 psi:**
- **U.S. Solid 1/4" NPT brass + Viton, 12V NC** — rated water/gas/oil/fuel, ~$15–25. Credible cheap fallback.
- **AceCrew 1/2" Viton NC** — explicitly lists propane/butane.
- ⚠️ Most generic "12V solenoid valves" are water/air only (NBR) — NOT fuel-rated. Require Viton + brass/SS for propane.

**Pneumatics / 100 psi + A/B exhaust (stretch):**
- **SMC SY3000** / **Festo VUVG** — compact 3/2 & 5/2, base/manifold-mountable. Best integration path: printed block = manifold base, valve island bolts on. ~$30–60/valve.

## Three insights that shape the spec

1. **Direct-acting is mandatory.** Pilot-operated valves need ~5–10 psi differential to open; won't work at low pressure / zero flow. Custom poppet must be coil-force-only. Caps practical orifice size per coil.
2. **NC = fail-safe but fights continuous duty.** De-energized = closed (spring) is the safe default, but coil must stay energized to keep flow on, and cheap solenoids overheat held on. **Flame-FX poofers rescue this** — brief energization = intermittent duty, where small cheap solenoids thrive. *Held* pneumatic cylinders are the hard case (continuous-duty or latching coil).
3. **Latching/bistable solenoids** — pulse to switch, zero holding power, no heat. Good for held-open cases; adds driver complexity.

**Net:** design the parametric block around a small continuous-duty 12V push-pull
(Makermotor-class), direct-acting, NC, gap-closes-at-seat — keep the U.S. Solid Viton
valve as a drop-in fallback in the same manifold footprint.

## Sources
- Makermotor PN00121: https://makermotor.com/pn00121-12vdc-push-pull-solenoid-actuator-6n-at-10mm-stroke-1-85a/
- Murphy RP2307B: https://catalog.baileymotorequip.com/item/engine-controls/solenoid-drivers/item-1195
- Geeplus push-pull range: https://www.geeplus.com/push-pull-solenoids/
- U.S. Solid 1/4" brass Viton NC: https://ussolid.com/products/u-s-solid-electric-solenoid-valve-1-4-12v-dc-solenoid-valve-brass-body-normally-closed-viton-seal-html
- AceCrew Viton (propane/butane): https://www.amazon.com/VITON-Brass-Solenoid-Normally-Closed/dp/B07C627DVM
- SMC SY3000 5-port: https://www.smcusa.com/products/sy3000-5-port-solenoid-valve-all-types~128914
- Festo valves/manifolds: https://www.festo.com/us/en/c/products/industrial-automation/pneumatic-valves-and-valve-manifolds-id_pim23/
- Direct-acting vs pilot (min. differential): https://ussolid.com/blogs/solenoid-valve/differences-between-pilot-operated-and-direct-acting-solenoid-valves
