import numpy as np
import pytest

from bioelectric_sim import ElectricalNetwork, SquarePulse, make_chain, simulate


def test_one_cell_matches_exact_passive_membrane_solution():
    network = ElectricalNetwork(
        capacitance_nF=[2.0],
        leak_conductance_uS=[0.1],
        leak_reversal_mV=[-70.0],
        gap_conductance_uS=[[0.0]],
    )
    initial_voltage = -30.0
    result = simulate(
        network,
        [initial_voltage],
        duration_ms=100.0,
        dt_ms=0.2,
        method="rk4",
    )
    exact = -70.0 + (initial_voltage + 70.0) * np.exp(
        -(0.1 / 2.0) * result.time_ms
    )
    np.testing.assert_allclose(result.voltage_mV[:, 0], exact, atol=2e-9)


def test_resting_network_stays_at_its_reversal_voltage():
    network = make_chain(cell_count=6)
    result = simulate(
        network,
        np.full(6, -70.0),
        duration_ms=50.0,
        dt_ms=0.1,
    )
    np.testing.assert_allclose(result.voltage_mV, -70.0, atol=1e-12)


def test_gap_current_is_pairwise_equal_and_opposite():
    network = make_chain(cell_count=4)
    current = network.gap_current_matrix_nA([-70.0, -50.0, -80.0, -65.0])
    np.testing.assert_allclose(current, -current.T, atol=1e-12)
    assert np.sum(current) == pytest.approx(0.0, abs=1e-12)


def test_gap_only_network_conserves_capacitance_weighted_voltage():
    network = ElectricalNetwork(
        capacitance_nF=[1.0, 2.0, 0.5],
        leak_conductance_uS=[0.0, 0.0, 0.0],
        leak_reversal_mV=[-70.0, -70.0, -70.0],
        gap_conductance_uS=[
            [0.0, 0.08, 0.0],
            [0.08, 0.0, 0.08],
            [0.0, 0.08, 0.0],
        ],
    )
    result = simulate(
        network,
        [-20.0, -70.0, -90.0],
        duration_ms=80.0,
        dt_ms=0.1,
    )
    charge_like_quantity = result.voltage_mV @ network.capacitance_nF
    np.testing.assert_allclose(
        charge_like_quantity, charge_like_quantity[0], atol=2e-11
    )


def test_square_pulse_uses_half_open_time_interval():
    pulse = SquarePulse(3, 1, 2.5, 10.0, 20.0)
    np.testing.assert_array_equal(pulse(9.999), [0.0, 0.0, 0.0])
    np.testing.assert_array_equal(pulse(10.0), [0.0, 2.5, 0.0])
    np.testing.assert_array_equal(pulse(19.999), [0.0, 2.5, 0.0])
    np.testing.assert_array_equal(pulse(20.0), [0.0, 0.0, 0.0])


def test_asymmetric_gap_junction_matrix_is_rejected():
    with pytest.raises(ValueError, match="symmetric"):
        ElectricalNetwork(
            capacitance_nF=[1.0, 1.0],
            leak_conductance_uS=[0.1, 0.1],
            leak_reversal_mV=[-70.0, -70.0],
            gap_conductance_uS=[[0.0, 0.1], [0.0, 0.0]],
        )


def test_last_step_is_shortened_to_reach_requested_duration():
    result = simulate(
        make_chain(cell_count=2),
        [-70.0, -70.0],
        duration_ms=1.0,
        dt_ms=0.3,
    )
    assert result.time_ms[-1] == pytest.approx(1.0)
    assert np.max(np.diff(result.time_ms)) <= 0.3 + 1e-12

