from qm.qua import *
from qm.quantum_machines_manager import QuantumMachinesManager
from qm import SimulationConfig, LoopbackInterface
import numpy as np
from .configuration_basic import config


def test_demodulation_work():
    with program() as prog:
        st = declare_stream()
        i = declare(int)
        v = declare(int)

        assign(v, 1)
        with for_(i, 0, i < 400, i + 1):
            save(v, st)

        with stream_processing():
            st.save_all(f"st")
            st.buffer(400).map(FUNCTIONS.demod(1, 1, 0)).save(f"st_demod")

    qmm = QuantumMachinesManager('localhost', 9510)
    job = qmm.simulate(
        config,
        prog,
        SimulationConfig(
            duration=10000,
            simulation_interface=LoopbackInterface([("con1", 3, "con1", 1)]),
        ),
    )
    job.result_handles.wait_for_all_values()

    st = job.result_handles.get("st").fetch_all()
    st_demod = job.result_handles.get("st_demod").fetch_all()

    assert np.array_equal(st["value"], np.array([1] * 400))
    assert np.allclose(st_demod, 400)


# def test_demodulation_work2():
#     freq = rr_IF
#
#     with program() as prog:
#         adc_st = declare_stream(adc_trace=True)
#         I_st = declare_stream()
#         Q_st = declare_stream()
#         i = declare(int)
#         I = declare(fixed)
#         Q = declare(fixed)
#
#         # 'integW1' and 'integW2' are simply 1 fro the length of measurement
#         measure('readout', 'rr', adc_st, demod.full('integW1', I),
#                 demod.full('integW2', Q))
#         save(I, I_st)
#         save(Q, Q_st)
#
#         with stream_processing():
#             adc_st.input1().save("a")
#             adc_st.input1().map(FUNCTIONS.demod(freq, 1.0, 0.0)).save(f"I_env")
#             adc_st.input1().map(FUNCTIONS.demod(freq, 0.0, 1.0)).save(f"Q_env")
#             I_st.save(f"I_st")
#             Q_st.save(f"Q_st")
#
#     qmm = QuantumMachinesManager()
#     job = qmm.simulate(config, prog, SimulationConfig(duration=100000,
#                                                       simulation_interface=LoopbackInterface(
#                                                           [("con1", 3, "con1", 1)])))
#     job.result_handles.wait_for_all_values()
#
#     a = job.result_handles.get("a").fetch_all()
#     I_sp = job.result_handles.get("I_env").fetch_all()
#     Q_sp = job.result_handles.get("Q_env").fetch_all()
#
#     I = job.result_handles.get("I_st").fetch_all()
#     Q = job.result_handles.get("Q_st").fetch_all()
#
#     assert np.allclose(np.sum(I_sp), I)
#     assert np.allclose(np.sum(Q_sp), Q)
