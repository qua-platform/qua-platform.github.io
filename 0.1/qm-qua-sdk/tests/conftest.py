import warnings
from contextlib import contextmanager

import pytest

from qm import DictQuaConfig
from qm.api.models.capabilities import ServerCapabilities
from qm.api.models.info import QuaMachineInfo, ImplementationInfo
from qm.containers.capabilities_container import create_capabilities_container


@contextmanager
def ignore_deprecation_warnings_context():
    warnings.simplefilter("ignore")
    yield
    warnings.simplefilter("default")


@pytest.fixture()
def ignore_deprecation():
    with ignore_deprecation_warnings_context():
        yield


@pytest.fixture(autouse=True)
def capability_container():
    container = create_capabilities_container(QuaMachineInfo([], ImplementationInfo("", "", "")))
    container.capabilities.override(ServerCapabilities(True, True, True, True, True, True, True, True, True, True, True,
                                                       True, True, True))
    return container


@pytest.fixture
def qua_bare_config() -> DictQuaConfig:
    return {
        'version': 1,
        'controllers': {
            'con1': {
                'type': 'opx1',
                'analog_outputs': {i: {'offset': 0.0} for i in range(1, 11)},
                'analog_inputs': {i: {'offset': 0.0} for i in range(1, 3)},
                'digital_outputs': {i: {} for i in range(1, 11)},
                "connectivity": "oct1",
            },
        },
        'octaves': {"oct1": {"loopbacks": []}},
        'elements': {},
    }
