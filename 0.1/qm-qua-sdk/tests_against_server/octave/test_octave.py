import pytest

from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.octave.octave_manager import OctaveManager
from qm.octave.octave_config import QmOctaveConfig
from tests.simulate.opx_config import config


@pytest.mark.skip("no simulated server yet")
def test_octave_init():
    octave_config = QmOctaveConfig()
    octave_config.add_device_info("octave1", "127.0.0.1", 333)
    octave_config.add_opx_octave_port_mapping(
        {("con1", 1): ("octave1", "I1"), ("con1", 2): ("octave1", "Q1")}
    )
    octave = OctaveManager(octave_config)


@pytest.mark.skip("playground")
def test_octave_with_qmm(host_port, tmpdir):
    from octave_sdk import OctaveLOSource, RFOutputMode, OctaveOutput
    octave_config = QmOctaveConfig()
    octave_config.add_device_info("octave1", "127.0.0.1", 80)
    octave_config.add_opx_octave_port_mapping({("con1", 1): ("octave1", "I1")})
    octave_config.set_calibration_db(tmpdir)
    octave_config.add_lo_loopback(
        "octave1", OctaveOutput.Synth3, "octave1", OctaveLOSource.LO1
    )

    qmm = QuantumMachinesManager(**host_port, octave=octave_config)

    qmm.octave_manager.set_clock()
    qmm.octave_manager.get_clock()
    qmm.octave_manager.restore_default_state()

    qm = qmm.open_qm(config, use_calibration_data=True)  # -> this can update the config inside
    qm.octave.set_element_rf_input("qb1", "octave1", 2)
    qm.octave.set_lo_source("qb1")
    qm.octave.set_lo_frequency("qb1",7e9)
    qm.octave.update_external_lo_frequency("qb1",8e9, OctaveLOSource.LO1)
    qm.octave.set_rf_output_gain("qb1", 6)
    qm.octave.set_rf_output_mode("qb1", RFOutputMode.on)
    qm.octave.set_downconversion_for_element("qb1")
    qm.octave.set_downconversion_lo("qb1", )
    qm.octave.load_lo_frequency_from_config("qb1")

    # qm.set_lo_frequency("qb1",7e9)
