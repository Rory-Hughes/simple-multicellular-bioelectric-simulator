"""Reusable, deliberately simple experiment definitions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .model import ElectricalNetwork


def make_chain(
    cell_count: int = 10,
    *,
    capacitance_nF: float = 1.0,
    leak_conductance_uS: float = 0.025,
    leak_reversal_mV: float = -70.0,
    gap_conductance_uS: float = 0.05,
) -> ElectricalNetwork:
    """Create a line of identical cells coupled to immediate neighbours."""

    if cell_count < 1:
        raise ValueError("cell_count must be at least one")
    gap = np.zeros((cell_count, cell_count), dtype=float)
    neighbour_indices = np.arange(cell_count - 1)
    gap[neighbour_indices, neighbour_indices + 1] = gap_conductance_uS
    gap[neighbour_indices + 1, neighbour_indices] = gap_conductance_uS
    return ElectricalNetwork(
        capacitance_nF=np.full(cell_count, capacitance_nF, dtype=float),
        leak_conductance_uS=np.full(cell_count, leak_conductance_uS, dtype=float),
        leak_reversal_mV=np.full(cell_count, leak_reversal_mV, dtype=float),
        gap_conductance_uS=gap,
    )


@dataclass(frozen=True)
class SquarePulse:
    """Inject a constant inward current into one cell over [start, end)."""

    cell_count: int
    cell_index: int
    amplitude_nA: float
    start_ms: float
    end_ms: float

    def __post_init__(self) -> None:
        if self.cell_count < 1:
            raise ValueError("cell_count must be at least one")
        if not 0 <= self.cell_index < self.cell_count:
            raise ValueError("cell_index is outside the network")
        if not np.isfinite(self.amplitude_nA):
            raise ValueError("amplitude_nA must be finite")
        if not 0 <= self.start_ms < self.end_ms:
            raise ValueError("pulse times must satisfy 0 <= start_ms < end_ms")

    def __call__(self, time_ms: float) -> NDArray[np.float64]:
        current = np.zeros(self.cell_count, dtype=float)
        if self.start_ms <= time_ms < self.end_ms:
            current[self.cell_index] = self.amplitude_nA
        return current

