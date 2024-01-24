from copy import deepcopy
from typing import Tuple, Callable
from unittest.mock import MagicMock

import pytest

import qm.octave.octave_manager
from octave_sdk import RFInputLOSource
from qm import DictQuaConfig
from qm.elements.up_converted_input import UpconvertedInput
from qm.elements.element_inputs import MixInputs
from qm.exceptions import (
    OctaveConnectionError,
    OctaveCableSwapError,
    ConfigValidationException,
    OctaveConnectionAmbiguity,
)
from qm.grpc.qua_config import QuaConfig
from qm.octave.octave_mixer_calibration import LOFrequencyCalibrationResult, LOFrequencyDebugData
from qm.quantum_machines_manager import QuantumMachinesManager
from qm.octave import OctaveOutput, OctaveLOSource
from qm.octave import octave_manager
import qm.octave.octave_config as config
from qm.program import load_config
from qm.program._qua_config_to_pb import load_config_pb
from qm.type_hinting.config_types import OctaveConfigType, ElementConfigType


@pytest.fixture
def qmm_with_octave(host_port, monkeypatch) -> QuantumMachinesManager:
    octave_config = config.QmOctaveConfig()
    octave_config.add_device_info("oct1", "127.0.0.1", 333)
    octave_mock = MagicMock()
    monkeypatch.setattr(f"qm.octave.octave_manager.Octave", octave_mock)
    return QuantumMachinesManager(**host_port, octave=octave_config)


@pytest.fixture
def octave_config_with_specific_connectivity() -> OctaveConfigType:
    return {
        "RF_outputs": {
            1: {
                "LO_frequency": 11e9,
                "LO_source": "internal",
                "output_mode": "always_on",
                "gain": -0.5,
                "input_attenuators": "ON",
                "I_connection": ("con1", 1),
                "Q_connection": ("con1", 2),
            },
            2: {
                "LO_frequency": 12e9,
                "LO_source": "external",
                "output_mode": "always_on",
                "gain": 1,
                "input_attenuators": "ON",
                "I_connection": ("con1", 3),
                "Q_connection": ("con1", 4),
            },
            3: {
                "LO_frequency": 13e9,
                "LO_source": "internal",
                "output_mode": "always_on",
                "gain": 1.5,
                "input_attenuators": "ON",
                "I_connection": ("con1", 5),
                "Q_connection": ("con1", 6),
            },
            4: {
                "LO_frequency": 14e9,
                "LO_source": "internal",
                "output_mode": "always_on",
                "gain": -3.5,
                "input_attenuators": "ON",
                "I_connection": ("con1", 7),
                "Q_connection": ("con1", 8),
            },
            5: {
                "LO_frequency": 15e9,
                "LO_source": "internal",
                "output_mode": "always_on",
                "gain": -4,
                "input_attenuators": "ON",
                "I_connection": ("con1", 9),
                "Q_connection": ("con1", 10),
            },
        },
        "RF_inputs": {
            1: {
                "RF_source": "RF_in",
                "LO_frequency": 16e9,
                "LO_source": "internal",
                "IF_mode_I": "direct",
                "IF_mode_Q": "direct",
            },
            2: {
                "RF_source": "RF_in",
                "LO_frequency": 17e9,
                "LO_source": "external",
                "IF_mode_I": "direct",
                "IF_mode_Q": "direct",
            },
        },
        "IF_outputs": {
            "IF_out1": {"port": ("con1", 1), "name": "moshe"},
            "IF_out2": {"port": ("con1", 2), "name": "haim"},
        },
    }


@pytest.fixture
def octave_minimal_config():
    return {
        "RF_outputs": {1: {"LO_frequency": 3e9, "gain": 1}, 3: {"LO_frequency": 4e9, "gain": 3}},
        "RF_inputs": {2: {"LO_frequency": 2e9}},
        "connectivity": "con1",
    }


@pytest.fixture
def qua_bare_config_with_minimal_octave(qua_bare_config, octave_minimal_config):
    qua_bare_config["octaves"] = {"oct1": octave_minimal_config}
    return qua_bare_config


@pytest.fixture
def qua_bare_config_with_specific_octave_connectivity(octave_config_with_specific_connectivity) -> DictQuaConfig:
    return {
        "version": 1,
        "controllers": {
            "con1": {
                "type": "opx1",
                "analog_outputs": {
                    1: {"offset": 0.0},
                    2: {"offset": 0.0},
                    3: {"offset": 0.0},
                    4: {"offset": 0.0},
                },
                "analog_inputs": {i: {"offset": 0.0} for i in range(1, 3)},
                "digital_outputs": {i: {} for i in range(1, 11)},
                "digital_inputs": {
                    i: {
                        "deadtime": 4,
                        "threshold": 0.5,
                        "polarity": "RISING",
                    }
                    for i in range(1, 3)
                },
            },
        },
        "octaves": {"oct1": octave_config_with_specific_connectivity},
        "elements": {},
    }


@pytest.fixture
def single_element_config() -> ElementConfigType:
    return {
        "mixInputs": {
            "I": ("con1", 1),
            "Q": ("con1", 2),
        },
        "intermediate_frequency": 456,
        "operations": {},
        "time_of_flight": 212,
        "smearing": 0,
        "outputs": {"out1": ("con1", 1)},
        "RF_outputs": {"out1": ("oct1", 1)},
    }


@pytest.fixture
def qua_single_element_config(qua_bare_config, single_element_config):
    qua_bare_config["elements"]["qe1"] = single_element_config
    return qua_bare_config


@pytest.fixture
def qua_single_element_with_octave_config(qua_bare_config_with_minimal_octave, single_element_config):
    qua_bare_config_with_minimal_octave["elements"]["qe1"] = single_element_config
    return qua_bare_config_with_minimal_octave


@pytest.fixture
def qua_single_element_config_with_specific_octave_connectivity(
    qua_bare_config_with_specific_octave_connectivity, single_element_config
):
    qua_bare_config_with_specific_octave_connectivity["elements"]["qe1"] = single_element_config
    return qua_bare_config_with_specific_octave_connectivity


@pytest.fixture
def qua_multiple_element_config_with_specific_octave_connectivity(
    qua_bare_config_with_specific_octave_connectivity, single_element_config
):
    qua_bare_config_with_specific_octave_connectivity["controllers"]["con1"]["analog_outputs"] = {
        i: {"offset": 0.0} for i in range(1, 11)
    }
    for i in range(1, 6):
        single_element = deepcopy(single_element_config)
        single_element["mixInputs"]["I"] = ("con1", 2 * i - 1)
        single_element["mixInputs"]["Q"] = ("con1", 2 * i)

        qua_bare_config_with_specific_octave_connectivity["elements"][f"qe{i}"] = single_element

    single_element = deepcopy(single_element_config)
    qua_bare_config_with_specific_octave_connectivity["elements"]["qe6"] = single_element
    # This duplication is to make sure that duplicates are fine
    return qua_bare_config_with_specific_octave_connectivity


pytestmark = pytest.mark.only_qop2


@pytest.mark.parametrize("config_loading_func", [load_config, load_config_pb])
def test_octave_config_opx(host_port, config_loading_func, qua_single_element_with_octave_config: dict):
    QuantumMachinesManager(**host_port)  # This line is here to initialize the Capabilities object
    config_pb = config_loading_func(qua_single_element_with_octave_config)

    rf_outputs = config_pb.v1_beta.octaves["oct1"].rf_outputs
    for idx, rf_output in rf_outputs.items():
        i_conn, q_conn = rf_output.i_connection, rf_output.q_connection
        assert (i_conn.controller, i_conn.number) == ("con1", 2 * idx - 1)
        assert (q_conn.controller, q_conn.number) == ("con1", 2 * idx)

    if_outputs = config_pb.v1_beta.octaves["oct1"].if_outputs
    if1, if2 = if_outputs.if_out1.port, if_outputs.if_out2.port
    assert (if1.controller, if1.number) == ("con1", 1)
    assert (if2.controller, if2.number) == ("con1", 2)


@pytest.mark.parametrize("loading_func", [load_config, load_config_pb])
def test_overriding_upconverter_default_config_raises_error(
    qmm_with_octave: QuantumMachinesManager,
    qua_bare_config_with_minimal_octave: DictQuaConfig,
    loading_func: Callable[[DictQuaConfig], QuaConfig],
):
    qua_bare_config_with_minimal_octave["octaves"]["oct1"]["RF_outputs"][1]["I_connection"] = ("con1", 1)
    with pytest.raises(OctaveConnectionAmbiguity):
        loading_func(qua_bare_config_with_minimal_octave)


@pytest.mark.parametrize("loading_func", [load_config, load_config_pb])
def test_overriding_downconverter_default_config_raises_error(
    qmm_with_octave: QuantumMachinesManager,
    qua_bare_config_with_minimal_octave: DictQuaConfig,
    loading_func: Callable[[DictQuaConfig], QuaConfig],
):
    qua_bare_config_with_minimal_octave["octaves"]["oct1"]["IF_outputs"] = {
        "IF_out1": {"port": ("con1", 1), "name": "IF_out1"}
    }
    with pytest.raises(OctaveConnectionAmbiguity):
        loading_func(qua_bare_config_with_minimal_octave)


@pytest.mark.parametrize(
    "I_conn",
    [
        ("con1", 1),
        ("con2", 2),
    ],
)
@pytest.mark.parametrize(
    "Q_conn",
    [
        ("con1", 3),
        ("con1", 4),
        ("con2", 4),
    ],
)
@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_octave_config_opx_bad_connections(
    host_port,
    qua_single_element_with_octave_config: DictQuaConfig,
    qmm_with_octave: QuantumMachinesManager,
    validate_with_protobuf: bool,
    I_conn: Tuple[str, int],
    Q_conn: Tuple[str, int],
) -> None:
    QuantumMachinesManager(**host_port)  # This line is here to initialize the Capabilities object
    qua_single_element_with_octave_config["octaves"]["oct1"]["RF_outputs"][1]["I_connection"] = I_conn
    qua_single_element_with_octave_config["octaves"]["oct1"]["RF_outputs"][1]["Q_connection"] = Q_conn
    with pytest.raises(OctaveConnectionAmbiguity):
        qmm_with_octave.open_qm(qua_single_element_with_octave_config, validate_with_protobuf=validate_with_protobuf)


@pytest.mark.parametrize("lo_freq", [1e9, 2e9])
@pytest.mark.parametrize("gain", [1.0, 3.14])
@pytest.mark.parametrize("octave_port", [("oct1", 1), ("oct3", 2)])
def test_octave_config_calibration_db(tmpdir, lo_freq: float, gain: float, octave_port: Tuple[str, int]):
    octave_config = config.QmOctaveConfig()
    octave_config.set_calibration_db(tmpdir)
    result = LOFrequencyCalibrationResult(
        debug=LOFrequencyDebugData(tuple(), None, [], []),
        i0=0.1,
        q0=0.2,
        dc_gain=0.5,
        dc_phase=0.6,
        temperature=0.7,
        image={},
    )
    result_dict = {(lo_freq, gain): result}
    octave_config.calibration_db.update_calibration_result(result_dict, octave_port)

    octave_config2 = config.QmOctaveConfig()
    octave_config2.set_calibration_db(tmpdir)
    query = octave_config2.calibration_db.get_lo_cal(octave_port, lo_freq, gain)
    assert query.i0 == result.i0
    assert query.q0 == result.q0
    assert query.dc_gain == result.dc_gain
    assert query.dc_phase == result.dc_phase
    assert query.temperature == result.temperature


@pytest.mark.parametrize("synth", [OctaveOutput.Synth1, OctaveOutput.Synth2, OctaveOutput.Synth3])
@pytest.mark.parametrize(
    "lo_source",
    [
        OctaveLOSource.LO1,
        OctaveLOSource.LO2,
        OctaveLOSource.LO3,
        OctaveLOSource.LO4,
        OctaveLOSource.LO5,
        OctaveLOSource.Dmd1LO,
        OctaveLOSource.Dmd2LO,
    ],
)
@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_octave_config_loop_backs(
    qmm_with_octave: QuantumMachinesManager,
    qua_single_element_with_octave_config: DictQuaConfig,
    synth: OctaveOutput,
    lo_source: OctaveLOSource,
    validate_with_protobuf: bool,
    monkeypatch,
):
    qm.octave.octave_manager._cached_get_device.cache_clear()
    qua_single_element_with_octave_config["octaves"]["oct1"]["loopbacks"] = [(("oct1", synth.name), lo_source.name)]

    qmm_with_octave.open_qm(config=qua_single_element_with_octave_config, validate_with_protobuf=validate_with_protobuf)

    octave_manager.Octave.assert_called_with(
        host="127.0.0.1",
        port=333,
        port_mapping={lo_source: synth},
        octave_name="oct1",
    )


@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_creating_an_element_not_connected_to_octave(
    qmm_with_octave: QuantumMachinesManager,
    validate_with_protobuf: bool,
    qua_bare_config_with_minimal_octave: dict,
):
    qua_bare_config_with_minimal_octave["elements"]["element_not_connected_to_octave"] = {
        "mixInputs": {
            "I": ("con1", 3),
            "Q": ("con1", 4),
            "lo_frequency": 123,
        },
        "intermediate_frequency": 456,
        "operations": {},
        "time_of_flight": 212,
        "smearing": 0,
        "outputs": {"out1": ("con1", 1)},
    }
    qm = qmm_with_octave.open_qm(
        config=qua_bare_config_with_minimal_octave, validate_with_protobuf=validate_with_protobuf
    )
    assert isinstance(qm._elements["element_not_connected_to_octave"].input, MixInputs)
    assert not isinstance(qm._elements["element_not_connected_to_octave"].input, UpconvertedInput)


@pytest.mark.parametrize(
    "i_conn",
    [
        ("con1", 2),
        ("con2", 1),
    ],
)
@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_failing_when_only_one_port_is_connected(
    i_conn: Tuple[str, int],
    qmm_with_octave: QuantumMachinesManager,
    qua_single_element_with_octave_config: DictQuaConfig,
    validate_with_protobuf: bool,
):
    qua_single_element_with_octave_config["elements"]["qe1"]["mixInputs"]["I"] = ("con1", 2)
    with pytest.raises(OctaveConnectionError):
        qmm_with_octave.open_qm(
            config=qua_single_element_with_octave_config, validate_with_protobuf=validate_with_protobuf
        )


@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_failing_when_cables_are_swapped(
    qmm_with_octave: QuantumMachinesManager,
    qua_single_element_with_octave_config: DictQuaConfig,
    validate_with_protobuf: bool,
):
    qua_single_element_with_octave_config["elements"]["qe1"]["mixInputs"]["I"] = ("con1", 2)
    qua_single_element_with_octave_config["elements"]["qe1"]["mixInputs"]["Q"] = ("con1", 1)
    with pytest.raises(OctaveCableSwapError):
        qmm_with_octave.open_qm(
            config=qua_single_element_with_octave_config, validate_with_protobuf=validate_with_protobuf
        )


@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_not_failing_even_if_improper_connection_when_not_relevant_to_experiment(
    qmm_with_octave: QuantumMachinesManager,
    qua_bare_config_with_specific_octave_connectivity: DictQuaConfig,
    validate_with_protobuf: bool,
    single_element_config: ElementConfigType,
):
    qua_bare_config_with_specific_octave_connectivity["octaves"]["oct1"]["RF_outputs"].pop(1)
    qua_bare_config_with_specific_octave_connectivity["octaves"]["oct1"]["RF_outputs"][3]["I_connection"] = ("con1", 3)

    qua_bare_config_with_specific_octave_connectivity["elements"][
        "element_not_connected_to_octave"
    ] = single_element_config
    qm = qmm_with_octave.open_qm(
        config=qua_bare_config_with_specific_octave_connectivity,
        validate_with_protobuf=validate_with_protobuf,
        add_calibration_elements_to_config=False,
    )
    assert isinstance(qm._elements["element_not_connected_to_octave"].input, MixInputs)
    assert not isinstance(qm._elements["element_not_connected_to_octave"].input, UpconvertedInput)


def test_two_loopbacks(host_port, monkeypatch) -> None:

    octave_mock = MagicMock()
    monkeypatch.setattr(f"qm.octave.octave_manager.Octave", octave_mock)

    octave_config = config.QmOctaveConfig()
    octave_config.add_device_info("oct1", "127.0.0.1", 333)
    octave_config.add_lo_loopback("oct1", OctaveOutput.Synth1, "oct1", OctaveLOSource.LO1)
    octave_config.add_lo_loopback("oct1", OctaveOutput.Synth2, "oct1", OctaveLOSource.LO2)
    QuantumMachinesManager(**host_port, octave=octave_config)


def test_setting_downconversion(qmm_with_octave, qua_single_element_with_octave_config):
    qm = qmm_with_octave.open_qm(qua_single_element_with_octave_config, add_calibration_elements_to_config=False)
    qm.octave.set_downconversion("qe1", RFInputLOSource.Off)


@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_many_elements(
    qmm_with_octave, qua_multiple_element_config_with_specific_octave_connectivity, validate_with_protobuf
):
    qm_inst = qmm_with_octave.open_qm(
        config=qua_multiple_element_config_with_specific_octave_connectivity,
        validate_with_protobuf=validate_with_protobuf,
    )
    for i in range(1, 6):
        element_input = qm_inst._elements[f"qe{i}"].input
        assert isinstance(element_input, UpconvertedInput)
        assert element_input.lo_frequency == (10 + i) * 1e9
        gain = qua_multiple_element_config_with_specific_octave_connectivity["octaves"]["oct1"]["RF_outputs"][i]["gain"]
        assert element_input.gain == gain

    element_input = qm_inst._elements[f"qe6"].input
    assert isinstance(element_input, UpconvertedInput)
    assert element_input.lo_frequency == 11e9
    gain = qua_multiple_element_config_with_specific_octave_connectivity["octaves"]["oct1"]["RF_outputs"][1]["gain"]
    assert element_input.gain == gain


@pytest.mark.parametrize("gain", [-21, 21, 1.1, -1.3])
@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_invalid_gain(
    gain, qmm_with_octave, qua_multiple_element_config_with_specific_octave_connectivity, validate_with_protobuf
):
    qua_multiple_element_config_with_specific_octave_connectivity["octaves"]["oct1"]["RF_outputs"][1]["gain"] = gain
    with pytest.raises(ConfigValidationException):
        qmm_with_octave.open_qm(
            config=qua_multiple_element_config_with_specific_octave_connectivity,
            validate_with_protobuf=validate_with_protobuf,
        )
