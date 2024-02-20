from qm import QuantumMachinesManager
from benchmark.config import MOCK_CONFIG
from qm.api.frontend_api import FrontendApi
from qm.api.models.server_details import ConnectionDetails
from qm.qua import program, declare, declare_stream, save, stream_processing, play

PORT = 1337
HOST = "127.0.0.1"


def test_benchmark_qmm_creation(benchmark, gateway_mock):
    benchmark.pedantic(QuantumMachinesManager, args=(HOST, PORT), rounds=10, iterations=10)


def test_benchmark_qm_creation(benchmark, gateway_mock):
    qmm = QuantumMachinesManager(HOST, PORT)
    benchmark.pedantic(qmm.open_qm, args=(MOCK_CONFIG,), rounds=10, iterations=10)


def test_benchmark_execute(benchmark, gateway_mock):
    qmm = QuantumMachinesManager(HOST, PORT)
    qm = qmm.open_qm(MOCK_CONFIG)

    with program() as prog:
        a = declare(int, value=1)
        b = declare_stream()
        save(a, b)
        play("pulse1", "qe1")
        with stream_processing():
            b.save('hello_stream')

    benchmark.pedantic(qm.execute, args=(prog,), rounds=10, iterations=10)


def test_communication(benchmark, gateway_mock):
    frontend_api = FrontendApi(ConnectionDetails(
        host=HOST,
        port=PORT,
        user_token=None,
        ssl_context=None
    ))
    benchmark(frontend_api.get_version)
