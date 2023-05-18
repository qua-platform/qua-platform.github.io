import logging
from unittest.mock import AsyncMock

import pytest

import qm.quantum_machines_manager
from qm.api.frontend_api import FrontendApi
from qm.api.models.info import QuaMachineInfo
from qm.api.models.server_details import ServerDetails, ConnectionDetails
from qm.api.simulation_api import SimulationApi


@pytest.fixture
def qmm_mock(monkeypatch, capability_container):
    monkeypatch.setattr(
        qm.quantum_machines_manager.QuantumMachinesManager,
        "_initialize_connection",
        lambda *x, **k: ServerDetails(
            host="mock-host",
            port=1234,
            qop_version="mock",
            connection_details=ConnectionDetails(
                host="mock-host",
                port=1234,
                ssl_context=None,
                user_token=None
            ),
            qua_implementation=None
        )
    )
    monkeypatch.setattr(qm.quantum_machines_manager, "FrontendApi", lambda x: AsyncMock())
    monkeypatch.setattr(qm.quantum_machines_manager, "SimulationApi", lambda x: AsyncMock())
    qmm = qm.quantum_machines_manager.QuantumMachinesManager(
        host="mock-host",
        port=1234,
        cluster_name="mock-cluster",
        log_level=logging.DEBUG
    )
    yield qmm