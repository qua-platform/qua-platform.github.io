from unittest.mock import AsyncMock

import pytest

from qm import QuantumMachine
from qm.api.job_manager_api import JobManagerApi
from qm.api.simulation_api import SimulationApi
from qm.octave.octave_manager import OctaveManager
from qm.persistence import SimpleFileStore
from qm.program._qua_config_to_pb import load_config_pb


@pytest.fixture
def mock_qm(qua_bare_config, capability_container, monkeypatch):
    monkeypatch.setattr(SimulationApi, "from_api", AsyncMock())
    monkeypatch.setattr(JobManagerApi, "from_api", AsyncMock())
    qm = QuantumMachine(
        machine_id='qm-1',
        pb_config=load_config_pb(qua_bare_config),
        frontend_api=AsyncMock(),
        capabilities=capability_container.capabilities,
        store=SimpleFileStore(),
        octave_manager=OctaveManager(),
        octave_config=None
    )
    return qm
