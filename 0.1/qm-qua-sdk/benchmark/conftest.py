import pytest

from qm.api.models.capabilities import ServerCapabilities
from qm.api.models.info import QuaMachineInfo, ImplementationInfo
from qm.containers.capabilities_container import create_capabilities_container
from tests.gateway_mock.gateway_mock import GatewayMock


@pytest.fixture(autouse=True)
def capability_container():
    container = create_capabilities_container(QuaMachineInfo([], ImplementationInfo("", "", "")))
    container.capabilities.override(ServerCapabilities(True, True, True, True, True, True, True, True, True, True, True,
                                                       True, True, True))
    return container


@pytest.fixture(scope="module")
def gateway_mock():
    gateway = GatewayMock()
    gateway.start()
    yield gateway
    gateway.stop()
