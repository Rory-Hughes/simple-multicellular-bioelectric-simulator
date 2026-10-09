"""Matplotlib views of already-computed simulation results."""

from __future__ import annotations

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.colors import Normalize
from matplotlib.figure import Figure

from .model import ElectricalNetwork, SimulationResult


def _voltage_limits(result: SimulationResult) -> tuple[float, float]:
    minimum = float(np.min(result.voltage_mV))
    maximum = float(np.max(result.voltage_mV))
    padding = max((maximum - minimum) * 0.08, 1.0)
    return minimum - padding, maximum + padding


def _draw_network_axis(
    axis, result: SimulationResult, network: ElectricalNetwork, sample_index: int
):
    x = np.arange(network.cell_count)
    for left in range(network.cell_count - 1):
        if network.gap_conductance_uS[left, left + 1] > 0:
            axis.plot([left, left + 1], [0, 0], color="0.68", linewidth=5, zorder=0)
    voltage_min, voltage_max = _voltage_limits(result)
    scatter = axis.scatter(
        x,
        np.zeros(network.cell_count),
        c=result.voltage_mV[sample_index],
        cmap="coolwarm",
        norm=Normalize(voltage_min, voltage_max),
        s=1150,
        edgecolor="black",
        linewidth=1.2,
        zorder=2,
    )
    for index in range(network.cell_count):
        axis.text(index, 0, str(index), ha="center", va="center", fontsize=9)
    axis.set_xlim(-0.75, max(network.cell_count - 0.25, 0.75))
    axis.set_ylim(-0.75, 0.75)
    axis.set_yticks([])
    axis.set_xlabel("Cell index (connections show model topology, not physical scale)")
    axis.spines[["left", "right", "top"]].set_visible(False)
    return scatter


def plot_summary(result: SimulationResult, network: ElectricalNetwork) -> Figure:
    """Create a static final-state and voltage-history figure."""

    figure, (network_axis, trace_axis) = plt.subplots(
        2, 1, figsize=(10, 6.5), gridspec_kw={"height_ratios": [1, 2]}, constrained_layout=True
    )
    scatter = _draw_network_axis(network_axis, result, network, -1)
    network_axis.set_title(f"Final state at {result.time_ms[-1]:.1f} ms")
    colorbar = figure.colorbar(scatter, ax=network_axis, orientation="horizontal", pad=0.28)
    colorbar.set_label("Membrane voltage (mV)")

    for cell_index in range(result.cell_count):
        trace_axis.plot(
            result.time_ms,
            result.voltage_mV[:, cell_index],
            label=f"Cell {cell_index}",
            linewidth=1.6,
        )
    trace_axis.set(xlabel="Simulation time (ms)", ylabel="Membrane voltage (mV)")
    trace_axis.grid(alpha=0.25)
    if result.cell_count <= 12:
        trace_axis.legend(ncol=min(5, result.cell_count), fontsize=8)
    return figure


def build_animation(
    result: SimulationResult,
    network: ElectricalNetwork,
    *,
    interval_ms: int = 35,
    maximum_frames: int = 500,
) -> tuple[Figure, FuncAnimation]:
    """Create an animation without changing or recomputing simulation state."""

    figure, (network_axis, trace_axis) = plt.subplots(
        2, 1, figsize=(10, 6.5), gridspec_kw={"height_ratios": [1, 2]}, constrained_layout=True
    )
    scatter = _draw_network_axis(network_axis, result, network, 0)
    colorbar = figure.colorbar(scatter, ax=network_axis, orientation="horizontal", pad=0.28)
    colorbar.set_label("Membrane voltage (mV)")

    trace_lines = []
    for cell_index in range(result.cell_count):
        (line,) = trace_axis.plot([], [], label=f"Cell {cell_index}", linewidth=1.6)
        trace_lines.append(line)
    voltage_min, voltage_max = _voltage_limits(result)
    trace_axis.set_xlim(float(result.time_ms[0]), float(result.time_ms[-1]))
    trace_axis.set_ylim(voltage_min, voltage_max)
    trace_axis.set(xlabel="Simulation time (ms)", ylabel="Membrane voltage (mV)")
    trace_axis.grid(alpha=0.25)
    if result.cell_count <= 12:
        trace_axis.legend(ncol=min(5, result.cell_count), fontsize=8)

    stride = max(1, int(np.ceil(result.time_ms.size / maximum_frames)))
    frame_indices = list(range(0, result.time_ms.size, stride))
    if frame_indices[-1] != result.time_ms.size - 1:
        frame_indices.append(result.time_ms.size - 1)

    def update(sample_index: int):
        scatter.set_array(result.voltage_mV[sample_index])
        network_axis.set_title(f"Simulation time: {result.time_ms[sample_index]:.1f} ms")
        for cell_index, line in enumerate(trace_lines):
            line.set_data(
                result.time_ms[: sample_index + 1],
                result.voltage_mV[: sample_index + 1, cell_index],
            )
        return [scatter, *trace_lines]

    animation = FuncAnimation(
        figure,
        update,
        frames=frame_indices,
        interval=interval_ms,
        repeat=True,
        blit=False,
    )
    return figure, animation


def show_animation(result: SimulationResult, network: ElectricalNetwork) -> None:
    """Open the interactive Matplotlib animation window."""

    _figure, animation = build_animation(result, network)
    # Retain a live reference until the blocking GUI call returns.
    _ = animation
    plt.show()

