import pytest

from qm import QuantumMachinesManager, SimulationConfig, CompilerOptionArguments
from qm.qua import program, save
from qm.simulate import loopback


def test_running_simulation_with_old_api(host_port, qua_bare_config):
    with program() as prog:
        save(1, "a")

    qmm = QuantumMachinesManager(**host_port)
    qmm.close_all_quantum_machines()
    qmm.simulate(qua_bare_config, prog, SimulationConfig(duration=100), flags=[], strict=False)


def test_using_both_apis_raises_error(host_port, qua_bare_config):
    with program() as prog:
        save(1, "a")

    qmm = QuantumMachinesManager(**host_port)
    qmm.close_all_quantum_machines()
    with pytest.raises(Exception):
        qmm.simulate(
            qua_bare_config,
            prog,
            SimulationConfig(duration=100, simulation_interface=loopback.LoopbackInterface([])),
            compiler_options=CompilerOptionArguments(),
            flags=[],
            strict=False,
        )
