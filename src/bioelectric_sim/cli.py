"""Command-line experiment runner."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Sequence

import numpy as np

from .model import SimulationResult, simulate
from .scenarios import SquarePulse, make_chain


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simulate a chain of passive, gap-junction-coupled cells."
    )
    parser.add_argument("--cells", type=int, default=10)
    parser.add_argument("--duration-ms", type=float, default=200.0)
    parser.add_argument("--dt-ms", type=float, default=0.1)
    parser.add_argument("--method", choices=("euler", "rk4"), default="rk4")
    parser.add_argument("--gap-conductance-us", type=float, default=0.05)
    parser.add_argument("--pulse-cell", type=int, default=0, help="zero-based cell index")
    parser.add_argument("--pulse-na", type=float, default=1.0)
    parser.add_argument("--pulse-start-ms", type=float, default=20.0)
    parser.add_argument("--pulse-end-ms", type=float, default=60.0)
    parser.add_argument("--csv", type=Path, help="write all numerical samples to CSV")
    parser.add_argument("--save-figure", type=Path, help="save a static PNG/SVG/PDF summary")
    parser.add_argument("--no-show", action="store_true", help="do not open the animation window")
    return parser


def _write_csv(path: Path, result: SimulationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_ms", *[f"cell_{i}_voltage_mV" for i in range(result.cell_count)]])
        for time, voltages in zip(result.time_ms, result.voltage_mV, strict=True):
            writer.writerow([time, *voltages])


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    network = make_chain(
        args.cells,
        gap_conductance_uS=args.gap_conductance_us,
    )
    pulse = SquarePulse(
        cell_count=network.cell_count,
        cell_index=args.pulse_cell,
        amplitude_nA=args.pulse_na,
        start_ms=args.pulse_start_ms,
        end_ms=args.pulse_end_ms,
    )
    result = simulate(
        network,
        np.full(network.cell_count, -70.0),
        duration_ms=args.duration_ms,
        dt_ms=args.dt_ms,
        stimulus=pulse,
        method=args.method,
    )

    print(
        f"Simulated {network.cell_count} cells for {result.time_ms[-1]:.1f} ms "
        f"({result.step_count} steps, {result.method})."
    )
    print(
        f"Observed voltage range: {np.min(result.voltage_mV):.3f} to "
        f"{np.max(result.voltage_mV):.3f} mV."
    )
    final = ", ".join(f"{value:.3f}" for value in result.voltage_mV[-1])
    print(f"Final cell voltages (mV): [{final}]")

    if args.csv is not None:
        _write_csv(args.csv, result)
        print(f"Wrote numerical trajectory to {args.csv.resolve()}")

    if args.save_figure is not None:
        from matplotlib import pyplot as plt

        from .visualization import plot_summary

        args.save_figure.parent.mkdir(parents=True, exist_ok=True)
        figure = plot_summary(result, network)
        figure.savefig(args.save_figure, dpi=160)
        plt.close(figure)
        print(f"Wrote summary figure to {args.save_figure.resolve()}")

    if not args.no_show:
        from .visualization import show_animation

        show_animation(result, network)
    return 0

