import pytest

from tests.conftest import ignore_warnings_context
from qm.quantum_machines_manager import QuantumMachinesManager
from qm.octave.octave_config import QmOctaveConfig
from tests.simulate.opx_config import create_opx_config


@pytest.mark.skip("no simulated server yet")
@pytest.mark.parametrize("validate_with_protobuf", [True, False])
def test_creating_an_element_with_octave_from_config(
    qmm_with_octave: QuantumMachinesManager,
    validate_with_protobuf: bool,
    qua_single_element_config: dict,
):
    with ignore_warnings_context():
        qmm_with_octave.open_qm(config=qua_single_element_config, validate_with_protobuf=validate_with_protobuf)
    assert True


@pytest.mark.skip("playground")
def test_octave_with_qmm(host_port, tmpdir):
    from octave_sdk import OctaveLOSource, RFOutputMode, OctaveOutput

    octave_config = QmOctaveConfig()
    octave_config.add_device_info("octave1", "127.0.0.1", 80)
    octave_config.add_opx_octave_port_mapping({("con1", 1): ("octave1", "I1")})
    octave_config.set_calibration_db(tmpdir)
    octave_config.add_lo_loopback("octave1", OctaveOutput.Synth3, "octave1", OctaveLOSource.LO1)

    qmm = QuantumMachinesManager(**host_port, octave=octave_config)

    qmm.octave_manager.set_clock()
    qmm.octave_manager.get_clock()
    qmm.octave_manager.restore_default_state()

    qm = qmm.open_qm(create_opx_config(), use_calibration_data=True)  # -> this can update the config inside
    qm.octave.set_element_rf_input("qb1", "octave1", 2)
    qm.octave.set_lo_source("qb1")
    qm.octave.set_lo_frequency("qb1", 7e9)
    qm.octave.update_external_lo_frequency("qb1", 8e9, OctaveLOSource.LO1)
    qm.octave.set_rf_output_gain("qb1", 6)
    qm.octave.set_rf_output_mode("qb1", RFOutputMode.on)
    qm.octave.set_downconversion_for_element("qb1")
    qm.octave.set_downconversion_lo(
        "qb1",
    )
    qm.octave.load_lo_frequency_from_config("qb1")

    # qm.set_lo_frequency("qb1",7e9)


def test_setting_an_attribute_both_element_and_gateway():
    pass


def test_two_elements_share_the_same_octave_different_ports():
    pass


def test_two_elements_share_ports():
    pass
