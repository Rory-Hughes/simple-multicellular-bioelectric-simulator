# Simple Multicellular Bioelectric Simulator

This is a small learning simulator, not a miniature BETSE. It models a chain of
cells as passive electrical membranes coupled by gap junctions, then renders the
computed voltages as an animation.

The first scientific question is intentionally narrow:

> If current depolarizes one cell, how does voltage spread through neighbouring
> cells and relax after the current stops?

## Run it

In PowerShell, from this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m bioelectric_sim
```

The upper panel is a symbolic cell chain. Cell colour is the simulated membrane
voltage in millivolts. The lower panel reveals the voltage history. The default
experiment injects `1 nA` into cell 0 from `20 ms` through (but not including)
`60 ms`.

For a numerical-only run and reproducible artifacts:

```powershell
python -m bioelectric_sim --no-show --csv outputs\run.csv --save-figure outputs\run.png
```

Try weakening the electrical coupling:

```powershell
python -m bioelectric_sim --gap-conductance-us 0.01
```

Then strengthen it:

```powershell
python -m bioelectric_sim --gap-conductance-us 0.15
```

The second experiment should spread voltage farther and make neighbouring cells
more alike. Predict the result before running it.

## The model

Each cell has one changing state variable, its membrane voltage `V_i`:

```text
C_i dV_i/dt = -g_L,i (V_i - E_L,i)
              + sum_j g_gap,ij (V_j - V_i)
              + I_external,i(t)
```

The terms mean:

- `C`: membrane capacitance; how much charge storage resists voltage change.
- `g_L` and `E_L`: a passive leak that pulls voltage toward its reversal value.
- `g_gap`: electrical coupling between neighbouring cells.
- `I_external`: an experimental current injected into a cell.

The unit convention is mV, ms, nF, uS, and nA. This is internally consistent:
`uS * mV = nA` and `nF * mV/ms = nA`.

The implementation offers Euler integration because it is easy to understand,
and fourth-order Runge-Kutta (`rk4`) as the more accurate default. Neither method
clips voltage or otherwise hides unstable parameter choices.

## What the picture does and does not mean

The visualization is directly tied to numerical state:

- colour encodes membrane voltage, and the colour bar states its units;
- the traces and cell colours use the same stored simulation result;
- the displayed time is simulated time, not animation playback time;
- connections show graph topology, not physical distance or cell size.

The circles are not realistic cell shapes. This version does not simulate ions,
ion pumps, voltage-gated channels, extracellular fields, gene expression,
mechanics, growth, or morphogenesis. A smooth-looking animation is not evidence
that the biology is realistic.

## Why the code is separated

```text
scenarios.py ---> model.py ---> SimulationResult ---> visualization.py
                       \\-----> tests / CSV output
```

`model.py` has no GUI dependency. The visualizer observes an already-computed
trajectory and cannot feed animation timing back into the physics.

## Validation already built in

Run:

```powershell
pytest
```

The checks cover:

- a one-cell passive membrane against its exact exponential solution;
- an equilibrium network that must remain unchanged;
- equal-and-opposite gap-junction current for every connected pair;
- conservation of capacitance-weighted voltage when only gap currents exist;
- stimulus timing, invalid network topology, and final-step handling.

These tests establish that the code solves the stated toy equations. They do not
validate the equations as a model of any particular biological tissue.

## Where to look first

- `src/bioelectric_sim/model.py`: equation, current calculations, and integrators.
- `src/bioelectric_sim/scenarios.py`: the chain and current pulse.
- `src/bioelectric_sim/visualization.py`: colour and trace rendering only.
- `tests/test_model.py`: executable scientific expectations.
- `docs/LEARNING_ROADMAP.md`: prerequisites, exercises, and the route to richer models.

