import os

import pytest

from qm.simulate.credentials import create_credentials


def pytest_addoption(parser):
    parser.addoption("--server_host", action="store", default="127.0.0.1")
    parser.addoption("--server_port", action="store", default=9510)
    parser.addoption("--use_ssl", action="store", default=False)
    parser.addoption("--qop1", action="store_true", default=False)


def pytest_generate_tests(metafunc):
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".
    for param in ["server_host", "server_port", "use_ssl"]:
        value = getattr(metafunc.config.option, param)
        if param in metafunc.fixturenames and value is not None:
            metafunc.parametrize(param, [value])


@pytest.fixture(scope="module", autouse=True)
def skip_qop1(request, pytestconfig):
    if request.node.get_closest_marker("only_qop2") is not None and pytestconfig.option.qop1:
        pytest.skip("")


@pytest.fixture(scope="function")
def host_port(server_host, server_port, server_credentials):
    return {"host": server_host, "port": server_port, "credentials": server_credentials}


@pytest.fixture(scope="function")
def server_credentials(use_ssl):
    return create_credentials() if use_ssl else None


@pytest.fixture
def qua_bare_config():
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
