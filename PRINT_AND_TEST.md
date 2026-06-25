# Print & bench-test guide

Goal: **prove one channel seals at 25 psi before printing the manifold.** Cheapest
possible learning — don't replicate an unsealed design.

## Parts & materials

| Part | File | Process / material | Notes |
|---|---|---|---|
| Valve body block | `build/solenoid_block.stl` | SLA, rigid resin | Orient coil bore up; supports off the +X outlet |
| Poppet | `build/poppet.stl` | SLA, rigid resin | Tiny — print a few spares |
| TPU gasket disc | `build/tpu_disc.stl` | **FDM, TPU 95A** (or flexible SLA resin) | Rigid SLA won't seal; needs an elastomer |
| 2-ch manifold | `build/manifold.stl` | SLA, rigid resin | Only after one channel passes |

> TPU is an **FDM** filament; the rigid parts are **SLA**. If you only have SLA, use a
> flexible resin for the gasket (Shore ~A80–95), or buy an O-ring (needs the wider-land
> variant — see `RESEARCH.md` / `BRIEF.md`).

## Bought hardware (per channel)

- 12V push-pull solenoid, **continuous-duty**, ~8 mm plunger, ~10 mm stroke
  (Makermotor PN00121 class). **Measure it and update `COIL_BORE_D` in `cad/solenoid_block.py`.**
- Return compression spring: OD ≈ 7 mm, free length ≈ 5–6 mm, **light** (~0.5–1 N). With
  the pressure-to-close layout it only reseats the poppet at zero pressure — supply
  pressure does the sealing. Sits in the chamber on the poppet top, bears on the ceiling.
  Don't oversize it: a stiff spring just makes the solenoid work harder to open.
- 4× M3 socket-head screws + heat-set inserts (for the manifold joint).
- Push-to-connect or barb fittings for the ports (tap the bottom inlet / +X outlet to taste).
- Thread sealant / PTFE tape rated for the medium.

## Assembly (single channel)

1. Press/glue the TPU disc into the poppet's bottom pocket (protrudes ~0.4 mm).
2. Bond the poppet onto the solenoid plunger tip (Ø8.1 bore). Verify the disc sits
   square — it must land flat on the Ø6 seat.
3. Drop the return spring into the chamber, insert poppet+plunger, seat the solenoid in
   the coil bore. De-energized, the spring must hold the poppet firmly on the seat.
4. Fit inlet/outlet fittings.

## Pressure test (do this BEFORE trusting it with propane)

**Test with AIR first. Never debug leaks with fuel gas.**

1. Cap the outlet. Connect a regulated air supply to the inlet through a gauge.
2. **Energize check:** at 0 psi, energize the coil — poppet should lift audibly/freely.
   De-energize — it must snap closed.
3. **Leak ramp:** apply 5 psi (de-energized). Brush soapy water over the seat area and
   every printed wall / joint. No bubbles = good. Hold 2 min, watch the gauge for decay.
4. Step to 10, then 25 psi (propane target), repeat the bubble + decay check at each step.
5. **Flow check:** open the outlet, energize — confirm full flow; de-energize — flow stops
   cleanly with no creep.
6. Only after a clean 25 psi hold should you consider propane (and only outdoors, with a
   regulator, leak detector, and a way to shut off upstream).

## What to watch / likely failure modes

- **Seat leak:** disc not flat, land print layer lines, or too little spring force.
  Try more gasket protrusion (raise `PROTRUDE` in `tpu_disc.py`) or a stiffer spring.
- **Wall weep:** SLA should be gas-tight; if it weeps, the print is under-cured or thin —
  thicken walls (raise the envelope) or re-cure.
- **Coil overheating:** if held energized for a flame *hold* (not a poof), the cheap coil
  may cook — see the duty-cycle notes in `RESEARCH.md`.

## Pneumatic / 100 psi note

Pressure-to-close means the coil must OPEN against P × orifice-area (+ light spring).
At 100 psi / Ø3 that's ≈ 4.9 N + ~1 N ≈ 6 N — right at a small coil's limit, but the
pull happens from the seated position where coil force peaks, so it's feasible. Bigger
pneumatic flow (larger orifice) needs a stronger coil or a pilot/3-way. The A/B+exhaust
2-way cylinder valve is a separate (stretch) block — not yet modeled.
