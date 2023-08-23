from typing import Tuple
from unittest.mock import MagicMock

import pytest

from qm.quantum_machines_manager import QuantumMachinesManager
from qm.elements.element_with_octave import ElementWithOctave
from qm.elements_db import OctaveConnectionError
from qm.octave import OctaveOutput, OctaveLOSource
from qm.octave.calibration_db import CalibrationResult
import qm.octave.octave_config as config
from qm.program import load_config
from qm.program._qua_config_to_pb import load_config_pb, OctaveConnectionAmbiguity


@pytest.fixture
def qmm_with_octave(host_port, monkeypatch) -> QuantumMachinesManager:
    octave_config = config.QmOctaveConfig()
    octave_config.add_device_info("oct1", "127.0.0.1", 333)
    octave_mock = MagicMock()
    monkeypatch.setattr(f"qm.octave.octave_config.Octave", octave_mock)
    return QuantumMachinesManager(**host_port, octave=octave_config)


@pytest.fixture
def qua_bare_config_with_specific_octave_connectivity():
    return {
        'version': 1,
        'controllers': {
            'con1': {
                'type': 'opx1',
                'analog_outputs': {
                    1: {'offset': 0.0, "connectivity": ("oct1", "I1")},
                    2: {'offset': 0.0, "connectivity": ("oct1", "Q1")},
                    3: {'offset': 0.0},
                    4: {'offset': 0.0},
                },
                'analog_inputs': {i: {'offset': 0.0} for i in range(1, 3)},
                'digital_outputs': {i: {} for i in range(1, 11)},
                'digital_inputs': {i:
                    {
                        "deadtime": 4,
                        "threshold": 0.5,
                        "polarity": "RISING",
                    } for i in range(1, 3)
                },
            },
        },
        'octaves': {"oct1": {"loopbacks": []}},
        'elements': {},
    }


@pytest.fixture
def qua_single_element_config(qua_bare_config):
    qua_bare_config["elements"]["qe1"] = {
        'mixInputs': {
            'I': ('con1', 1),
            'Q': ('con1', 2),
            'lo_frequency': 123,
            "octave_params": {
                "lo_source": "Internal",
                "rf_output_port": ("oct1", "RF1"),
                "rf_input_port": ("oct1", "RF_IN1")
            }
        },
        'intermediate_frequency': 456,
        'operations': {},
        'time_of_flight': 212,
        'smearing': 0,
        'outputs': {'out1': ('con1', 1)}
    }
    return qua_bare_config


pytestmark = pytest.mark.only_qop2


@pytest.mark.parametrize("config_loading_func", [load_config, load_config_pb])
def test_octave_config_opx(host_port, config_loading_func, qua_single_element_config: dict):
    QuantumMachinesManager(**host_port)  # This line is here to initialize the Capabilities object
    config_pb = config_loading_func(qua_single_element_config)

    analog_outputs = config_pb.v1_beta.controllers["con1"].analog_outputs
    for idx, output in analog_outputs.items():
        assert output.octave_connectivity.device_name == "oct1"
        assert output.octave_connectivity.port_name.name == ["Q", "I"][idx % 2] + str((idx + 1) // 2)

    analog_inputs = config_pb.v1_beta.controllers["con1"].analog_inputs
    for idx, input_ in analog_inputs.items():
        assert input_.octave_connectivity.device_name == "oct1"
        assert input_.octave_connectivity.port_name.name == f"IF{idx}"


@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_overriding_default_config_raises_error(
    qmm_with_octave: QuantumMachinesManager,
    validate_with_protobuf: bool,
    qua_single_element_config: dict
):
    qua_single_element_config['controllers']['con1']['analog_outputs'][1]["connectivity"] = ("oct1", "I1")
    qua_single_element_config['controllers']['con1']['analog_outputs'][2]["connectivity"] = ("oct1", "Q1")
    with pytest.raises(OctaveConnectionAmbiguity):
        qmm_with_octave.open_qm(config=qua_single_element_config, validate_with_protobuf=validate_with_protobuf)


@pytest.mark.parametrize(
    "p1_conn",
    [
        ("oct1", "I1"),
        ("oct2", "Q1"),
    ]
)
@pytest.mark.parametrize(
    "p2_conn",
    [
        ("oct1", "I2"),
        ("oct1", "Q2"),
        ("oct2", "Q1"),
    ]
)
@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_octave_config_opx_bad_connections(
    qmm_with_octave: QuantumMachinesManager, qua_single_element_config: dict,
    p1_conn: Tuple[str, str], p2_conn: Tuple[str, str], validate_with_protobuf: bool
):
    qua_single_element_config['controllers']['con1'].pop("connectivity")
    qua_single_element_config['controllers']['con1']['analog_outputs'][1]["connectivity"] = p1_conn
    qua_single_element_config['controllers']['con1']['analog_outputs'][2]["connectivity"] = p2_conn
    with pytest.raises(OctaveConnectionError):
        qmm_with_octave.open_qm(config=qua_single_element_config, validate_with_protobuf=validate_with_protobuf)


def test_octave_config_calibration_db(tmpdir):
    octave_config = config.QmOctaveConfig()
    octave_config.set_calibration_db(tmpdir)
    result = CalibrationResult([0.1, 0.2, 0.3, 0.4], 0.01, -0.01, 2e9, 50e6, 6.0, "mixer", {})
    octave_config.calibration_db.update_calibration_data(result)

    octave_config2 = config.QmOctaveConfig()
    octave_config2.set_calibration_db(tmpdir)
    query = octave_config2.calibration_db.get_all("mixer")
    assert len(query) == 1
    assert query[0] == result


@pytest.mark.parametrize(
    "synth",
    [
        OctaveOutput.Synth1,
        OctaveOutput.Synth2,
        OctaveOutput.Synth3
    ]
)
@pytest.mark.parametrize(
    "lo_source",
    [
        OctaveLOSource.LO1,
        OctaveLOSource.LO2,
        OctaveLOSource.LO3,
        OctaveLOSource.LO4,
        OctaveLOSource.LO5
    ]
)
@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_octave_config_loop_backs(
    qmm_with_octave: QuantumMachinesManager,
    qua_single_element_config: dict,
    synth: OctaveOutput, lo_source: OctaveLOSource, validate_with_protobuf: bool, monkeypatch
):
    config._cached_get_device.cache_clear()
    qua_single_element_config["octaves"] = {"oct1": {"loopbacks": [(("oct1", synth.name), lo_source.name)]}}

    qmm_with_octave.open_qm(config=qua_single_element_config, validate_with_protobuf=validate_with_protobuf)

    config.Octave.assert_called_with(
        host="127.0.0.1",
        port=333,
        port_mapping={lo_source: synth},
        octave_name="oct1",
    )


@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_creating_an_element_not_connected_to_octave(
    qmm_with_octave: QuantumMachinesManager,
    validate_with_protobuf: bool,
    qua_bare_config_with_specific_octave_connectivity: dict,
):
    qua_bare_config_with_specific_octave_connectivity["elements"]["element_not_connected_to_octave"] = {
        'mixInputs': {
            'I': ('con1', 3),
            'Q': ('con1', 4),
            'lo_frequency': 123,
        },
        'intermediate_frequency': 456,
        'operations': {},
        'time_of_flight': 212,
        'smearing': 0,
        'outputs': {'out1': ('con1', 1)}
    }
    qm = qmm_with_octave.open_qm(
        config=qua_bare_config_with_specific_octave_connectivity, validate_with_protobuf=validate_with_protobuf)
    assert not isinstance(qm.elements["element_not_connected_to_octave"], ElementWithOctave)


def test_creating_an_element_without_octave_config():
    pass


@pytest.mark.parametrize(
    "p1_conn",
    [
        ("oct1", "I1"),
        ("oct2", "Q1"),
    ]
)
@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_failing_when_only_one_port_is_connected(
    p1_conn: Tuple[str, str],
    qmm_with_octave: QuantumMachinesManager, qua_single_element_config: dict,
    validate_with_protobuf: bool
):
    qua_single_element_config['controllers']['con1'].pop("connectivity")
    qua_single_element_config['controllers']['con1']['analog_outputs'][1]["connectivity"] = p1_conn
    with pytest.raises(OctaveConnectionError):
        qmm_with_octave.open_qm(config=qua_single_element_config, validate_with_protobuf=validate_with_protobuf)


@pytest.mark.parametrize(
    "p1_conn",
    [
        ("oct1", "I1"),
        ("oct2", "Q1"),
    ]
)
@pytest.mark.parametrize(
    "p2_conn",
    [
        ("oct1", "I2"),
        ("oct1", "Q2"),
        ("oct2", "Q1"),
    ]
)
@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_not_failing_even_if_improper_connection_when_not_relevant_to_experiment(
    qmm_with_octave: QuantumMachinesManager,
    qua_bare_config_with_specific_octave_connectivity: dict,
    p1_conn: Tuple[str, str], p2_conn: Tuple[str, str], validate_with_protobuf: bool
):
    qua_bare_config_with_specific_octave_connectivity['controllers']['con1']['analog_outputs'][1][
        "connectivity"] = p1_conn
    qua_bare_config_with_specific_octave_connectivity['controllers']['con1']['analog_outputs'][2][
        "connectivity"] = p2_conn
    qua_bare_config_with_specific_octave_connectivity["elements"]["element_not_connected_to_octave"] = {
        'mixInputs': {
            'I': ('con1', 3),
            'Q': ('con1', 4),
            'lo_frequency': 123,
        },
        'intermediate_frequency': 456,
        'operations': {},
        'time_of_flight': 212,
        'smearing': 0,
        'outputs': {'out1': ('con1', 1)}
    }
    qm = qmm_with_octave.open_qm(
        config=qua_bare_config_with_specific_octave_connectivity, validate_with_protobuf=validate_with_protobuf)
    assert not isinstance(qm.elements["element_not_connected_to_octave"], ElementWithOctave)


def test_contradicting_elements():
    pass
