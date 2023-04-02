from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from tests.simulate.opx_config import config
from qm.simulate.interface import SimulationConfig
from qm.simulate import loopback


def test_result_handles_work(host_port):
    with program() as prog1:
        I = declare(int)
        Q = declare(int)
        assign(I, 10)
        assign(Q, 30)
        save(I, "I")
        save(Q, "Q")

    qmm = QuantumMachinesManager(**host_port)
    qmm.close_all_quantum_machines()
    job = qmm.simulate(
        config,
        prog1,
        SimulationConfig(
            duration=100, simulation_interface=loopback.LoopbackInterface([])
        ),
    )
    job.result_handles.wait_for_all_values()
    assert 10 == job.result_handles.I.fetch_all()[0][0]
    assert 30 == job.result_handles.Q.fetch_all()[0][0]
