"""Numerical model for electrically coupled, passive cells.

The renderer deliberately does not appear in this module.  This module only
knows about voltages, currents, parameters, and time.

Unit convention
---------------
voltage:      millivolts (mV)
time:         milliseconds (ms)
capacitance:  nanofarads (nF)
conductance:  microsiemens (uS)
current:      nanoamps (nA)

With these units, uS * mV = nA and nF * mV / ms = nA.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]
IntegrationMethod = Literal["euler", "rk4"]
Stimulus = Callable[[float], ArrayLike]


def _vector(name: str, values: ArrayLike, size: int | None = None) -> FloatArray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{name} must be a one-dimensional array")
    if size is not None and array.shape != (size,):
        raise ValueError(f"{name} must contain exactly {size} values")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array.copy()


@dataclass(frozen=True)
class CurrentComponents:
    """Currents entering each cell under the model's sign convention."""

    leak_nA: FloatArray
    gap_junction_nA: FloatArray
    external_nA: FloatArray

    @property
    def total_nA(self) -> FloatArray:
        return self.leak_nA + self.gap_junction_nA + self.external_nA


@dataclass(frozen=True)
class ElectricalNetwork:
    """Parameters for a network of passive, gap-junction-coupled cells."""

    capacitance_nF: ArrayLike
    leak_conductance_uS: ArrayLike
    leak_reversal_mV: ArrayLike
    gap_conductance_uS: ArrayLike

    def __post_init__(self) -> None:
        capacitance = _vector("capacitance_nF", self.capacitance_nF)
        cell_count = capacitance.size
        if cell_count == 0:
            raise ValueError("the network must contain at least one cell")

        leak_conductance = _vector(
            "leak_conductance_uS", self.leak_conductance_uS, cell_count
        )
        leak_reversal = _vector(
            "leak_reversal_mV", self.leak_reversal_mV, cell_count
        )
        gap_conductance = np.asarray(self.gap_conductance_uS, dtype=float)

        if gap_conductance.shape != (cell_count, cell_count):
            raise ValueError(
                "gap_conductance_uS must be a square cell_count x cell_count matrix"
            )
        if not np.all(np.isfinite(gap_conductance)):
            raise ValueError("gap_conductance_uS must contain only finite values")
        if np.any(capacitance <= 0):
            raise ValueError("every membrane capacitance must be positive")
        if np.any(leak_conductance < 0) or np.any(gap_conductance < 0):
            raise ValueError("conductances cannot be negative")
        if not np.allclose(gap_conductance, gap_conductance.T, atol=1e-12):
            raise ValueError("gap-junction conductance must be symmetric")
        if not np.allclose(np.diag(gap_conductance), 0.0, atol=1e-12):
            raise ValueError("a cell cannot have a gap junction to itself")

        object.__setattr__(self, "capacitance_nF", capacitance)
        object.__setattr__(self, "leak_conductance_uS", leak_conductance)
        object.__setattr__(self, "leak_reversal_mV", leak_reversal)
        object.__setattr__(self, "gap_conductance_uS", gap_conductance.copy())

    @property
    def cell_count(self) -> int:
        return int(self.capacitance_nF.size)

    def gap_current_matrix_nA(self, voltage_mV: ArrayLike) -> FloatArray:
        """Return current into cell i from cell j at matrix position [i, j]."""

        voltage = _vector("voltage_mV", voltage_mV, self.cell_count)
        voltage_difference = voltage[np.newaxis, :] - voltage[:, np.newaxis]
        return self.gap_conductance_uS * voltage_difference

    def current_components(
        self, voltage_mV: ArrayLike, external_current_nA: ArrayLike | None = None
    ) -> CurrentComponents:
        """Calculate inward-positive leak, coupling, and applied currents."""

        voltage = _vector("voltage_mV", voltage_mV, self.cell_count)
        external = (
            np.zeros(self.cell_count, dtype=float)
            if external_current_nA is None
            else _vector("external_current_nA", external_current_nA, self.cell_count)
        )
        leak = -self.leak_conductance_uS * (voltage - self.leak_reversal_mV)
        gap = self.gap_current_matrix_nA(voltage).sum(axis=1)
        return CurrentComponents(leak, gap, external)

    def voltage_derivative_mV_per_ms(
        self, voltage_mV: ArrayLike, external_current_nA: ArrayLike | None = None
    ) -> FloatArray:
        currents = self.current_components(voltage_mV, external_current_nA)
        return currents.total_nA / self.capacitance_nF


@dataclass(frozen=True)
class SimulationResult:
    """Complete sampled trajectory returned by :func:`simulate`."""

    time_ms: FloatArray
    voltage_mV: FloatArray
    external_current_nA: FloatArray
    method: IntegrationMethod

    @property
    def cell_count(self) -> int:
        return int(self.voltage_mV.shape[1])

    @property
    def step_count(self) -> int:
        return int(self.time_ms.size - 1)


def _sample_stimulus(
    stimulus: Stimulus | None, time_ms: float, cell_count: int
) -> FloatArray:
    if stimulus is None:
        return np.zeros(cell_count, dtype=float)
    return _vector("stimulus result", stimulus(time_ms), cell_count)


def _time_points(duration_ms: float, dt_ms: float) -> FloatArray:
    if not np.isfinite(duration_ms) or duration_ms <= 0:
        raise ValueError("duration_ms must be finite and positive")
    if not np.isfinite(dt_ms) or dt_ms <= 0:
        raise ValueError("dt_ms must be finite and positive")

    full_step_count = int(np.floor(duration_ms / dt_ms))
    points = np.arange(full_step_count + 1, dtype=float) * dt_ms
    tolerance = np.finfo(float).eps * max(duration_ms, 1.0) * 8
    if duration_ms - points[-1] > tolerance:
        points = np.append(points, duration_ms)
    else:
        points[-1] = duration_ms
    return points


def simulate(
    network: ElectricalNetwork,
    initial_voltage_mV: ArrayLike,
    *,
    duration_ms: float,
    dt_ms: float,
    stimulus: Stimulus | None = None,
    method: IntegrationMethod = "rk4",
) -> SimulationResult:
    """Integrate the network equation and return every sampled state.

    ``dt_ms`` is the maximum time step.  If it does not divide the requested
    duration exactly, the final step is shortened so the final time is exact.
    """

    if method not in ("euler", "rk4"):
        raise ValueError("method must be 'euler' or 'rk4'")

    initial = _vector("initial_voltage_mV", initial_voltage_mV, network.cell_count)
    time = _time_points(duration_ms, dt_ms)
    voltage = np.empty((time.size, network.cell_count), dtype=float)
    external_current = np.empty_like(voltage)
    voltage[0] = initial

    def derivative(t: float, state: FloatArray) -> FloatArray:
        current = _sample_stimulus(stimulus, t, network.cell_count)
        return network.voltage_derivative_mV_per_ms(state, current)

    for index in range(time.size - 1):
        t = float(time[index])
        h = float(time[index + 1] - time[index])
        state = voltage[index]
        external_current[index] = _sample_stimulus(stimulus, t, network.cell_count)

        if method == "euler":
            next_state = state + h * derivative(t, state)
        else:
            k1 = derivative(t, state)
            k2 = derivative(t + h / 2, state + h * k1 / 2)
            k3 = derivative(t + h / 2, state + h * k2 / 2)
            k4 = derivative(t + h, state + h * k3)
            next_state = state + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6

        if not np.all(np.isfinite(next_state)):
            raise FloatingPointError(
                "the simulation became non-finite; reduce dt_ms or inspect parameters"
            )
        voltage[index + 1] = next_state

    external_current[-1] = _sample_stimulus(
        stimulus, float(time[-1]), network.cell_count
    )
    return SimulationResult(time, voltage, external_current, method)

