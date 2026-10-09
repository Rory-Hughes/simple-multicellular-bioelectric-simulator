# Learning Roadmap: Build First, Study on Demand

You do not need calculus mastery, electrophysiology, or numerical-analysis
coursework before changing this simulator. You need just enough vocabulary to
form a prediction, make one controlled change, and explain the output.

## Bare minimum before the first run

Understand these ideas at an intuitive level:

1. A Python list or NumPy array can hold one voltage per cell.
2. A function maps inputs to outputs; a derivative is a rate of change.
3. Positive injected current raises voltage under this model's sign convention.
4. A conductance produces more current when the voltage difference is larger.
5. A smaller numerical time step normally costs more computation but reduces
   integration error.

That is enough to run the code and begin experimenting.

## Stage 1: one passive cell

Concepts to learn:

- voltage as electrical potential difference;
- current as movement of charge;
- capacitance as charge storage;
- conductance as the inverse of resistance;
- exponential relaxation and the time constant `tau = C / g_L`.

Depth target: explain why changing `C`, `g_L`, or `E_L` changes the curve, and
predict the direction of each change before running it.

Understanding checks:

- Set `cell_count=1` in a small script and remove the pulse. Start away from
  `E_L`. Does it return halfway to rest at the time you predicted?
- Halve `C`. Does relaxation become twice as fast?
- Read `test_one_cell_matches_exact_passive_membrane_solution` and connect each
  code term to the equation.

## Stage 2: a chain of coupled cells

Concepts to learn:

- a graph represented by a symmetric adjacency/conductance matrix;
- pairwise current `g_gap (V_j - V_i)`;
- conservation: current leaving one cell enters the other;
- spatial attenuation caused by the combination of coupling and leak.

Depth target: calculate the sign of the gap current between two given voltages,
and predict how stronger coupling changes voltage differences.

Understanding checks:

- Compare `--gap-conductance-us 0`, `0.01`, `0.05`, and `0.15`.
- Move the pulse from cell 0 to cell 5. Explain the symmetry or asymmetry.
- Give one cell a different leak reversal voltage and predict the resting pattern.

## Stage 3: numerical methods

Concepts to learn:

- an ordinary differential equation defines a rate, not the whole trajectory;
- Euler's method follows the local slope one step at a time;
- truncation error, convergence, and instability;
- why comparison to an analytic solution is stronger than visual plausibility.

Depth target: implement Euler's update on paper, identify when a result changes
materially with `dt_ms`, and perform a time-step convergence check.

Understanding checks:

- Compare `--method euler` with `--method rk4` at several step sizes.
- Keep halving `dt_ms`. A trustworthy result should converge.
- Deliberately make Euler unstable, then explain why the oscillation or blow-up
  is numerical rather than biological.

## Stage 4: biological enrichment, one mechanism at a time

Add mechanisms in this order only after the simpler model has a test:

1. Heterogeneous cells with different leak parameters.
2. A two-dimensional grid or tissue graph.
3. A voltage-dependent conductance producing bistable voltage states.
4. Voltage-dependent gap-junction gating.
5. Explicit ion concentrations and Nernst reversal potentials.
6. Pumps and cotransporters, with mass/charge balance checks.
7. Coupling from voltage to gene-regulatory or reaction-diffusion state.
8. Only then, a carefully stated toy model of pattern or morphology.

At every stage, write down:

- the biological claim;
- the equation and units;
- the parameter source or clearly marked assumption;
- the limiting case that should have a known answer;
- the visualization mapping;
- what the model still cannot support as a conclusion.

## A useful lab-notebook template

For every experiment, record:

```text
Question:
Prediction:
Parameters changed:
Parameters held fixed:
Numerical method and dt:
Observed result:
Time-step convergence result:
Interpretation:
Alternative explanation:
Next test:
```

This turns exploratory coding into the beginning of reproducible computational
science rather than a collection of attractive animations.

## Resources, in the order they become useful

These are deliberately matched to project milestones. Do not wait to finish an
entire course before experimenting.

1. **Python:** use the official [Python Tutorial](https://docs.python.org/3/tutorial/)
   as a reference. For this project, stop after you are comfortable with control
   flow, functions, lists, modules, and basic classes. You do not need advanced
   object-oriented design or metaprogramming.
2. **Scientific arrays:** work through NumPy's [absolute beginner's
   guide](https://numpy.org/doc/stable/user/absolute_beginners.html) through array
   creation, shape, indexing, and element-wise operations. Then explain the shapes
   of the voltage vector and gap-conductance matrix in `model.py`.
3. **Membrane voltage:** read [Electrical Potentials Across Nerve Cell
   Membranes](https://www.ncbi.nlm.nih.gov/books/NBK11069/) from the NCBI Bookshelf
   for biological grounding. Initially aim to distinguish membrane potential,
   equilibrium potential, and ionic concentration gradient; a full derivation of
   every electrochemical equation can wait for Stage 4.
4. **Differential equations:** use MIT OpenCourseWare's [18.03SC Differential
   Equations](https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/)
   selectively. Begin with first-order linear equations and numerical methods.
   Your practical stopping point is being able to derive and interpret the
   one-cell exponential relaxation test.
5. **Visualization:** consult Matplotlib's [animation
   guide](https://matplotlib.org/stable/users/explain/animations/index.html) only
   after you can inspect the numerical result. Compare its frame-update pattern
   with `build_animation`; confirm that rendering never advances model time.
6. **The destination, not the starting point:** read Pietak and Levin's
   [BETSE paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC4933718/) first for its
   conceptual scope and validation strategy. Return to its mathematical details
   only when adding explicit ions, electrodiffusion, or extracellular space.

For every resource, produce something observable: annotate an equation, change a
parameter, add a test, or explain a plot. Passive reading is not a completion
criterion.
