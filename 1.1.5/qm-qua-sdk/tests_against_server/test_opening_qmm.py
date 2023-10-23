import pytest
import asyncio

from qm.quantum_machines_manager import QuantumMachinesManager
from qm.exceptions import QmServerDetectionError, QMConnectionError


def test_fail_to_connect_wrong_host(host_port):
    with pytest.raises(QmServerDetectionError, match="Failed to detect a QuantumMachines server. Tried connecting to 1.2.3.4:9510."):
        host_port["host"] = "1.2.3.4"
        QuantumMachinesManager(**host_port, timeout=2)


def test_fail_to_connect_wrong_port(host_port):
    with pytest.raises(QmServerDetectionError, match="Failed to detect a QuantumMachines server."):
        new_host_port = {**host_port}
        new_host_port["port"] = host_port["port"] + 1
        QuantumMachinesManager(**new_host_port)


def test_we_can_open_qmm(host_port, server_credentials):
    qmm = QuantumMachinesManager(**host_port)


def test_we_can_open_qmm_inside_event_loop(host_port, server_credentials):
    async def run_me():
        qmm = QuantumMachinesManager(**host_port)

    asyncio.run(run_me())


def test_we_can_open_qmm_and_get_event_loop_fails(host_port, server_credentials):
    QuantumMachinesManager(**host_port)
    with pytest.raises(Exception):
        asyncio.get_running_loop()


def test_we_can_open_qmm_and_use_asyncio_run(host_port, server_credentials):
    async def run_me():
        QuantumMachinesManager(**host_port)

    QuantumMachinesManager(**host_port)
    asyncio.run(run_me())
    QuantumMachinesManager(**host_port)
    asyncio.run(run_me())
