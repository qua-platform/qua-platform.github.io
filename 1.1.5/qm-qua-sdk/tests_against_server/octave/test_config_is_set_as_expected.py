import os
import pytest
from unittest.mock import MagicMock

from qm import QuantumMachinesManager
from qm.octave import QmOctaveConfig

check_up_converters = False
calibration = False

controller_name = "con1"
octave_name = "octave1"


config = {
    "version": 1,
    "controllers": {
        controller_name: {
            "analog_outputs": {3: {"offset": 0.0}, 4: {"offset": 0.0}},
            "analog_inputs": {1: {"offset": 0.0}, 2: {"offset": 0.0}},
        }
    },
    "elements": {
        "qe2": {
            "RF_inputs": {"port": (octave_name, 2)},
            "intermediate_frequency": 50e6,
        },
    },
    "octaves": {
        octave_name: {
            "RF_outputs": {
                2: {
                    "LO_frequency": 5e9,
                    "LO_source": "internal",
                    "output_mode": "always_on",
                    "gain": 0,
                },
            },
            "connectivity": controller_name,
        }
    },
    "pulses": {},
    "waveforms": {},
    "digital_waveforms": {},
    "integration_weights": {},
}


pytestmark = pytest.mark.only_qop2


def test_config_is_set_as_expected(monkeypatch, host_port):
    """This test checks that when adding the calibration elements to the config, the config is not changed"""
    octave_config = QmOctaveConfig()
    octave_config.add_device_info("octave1", "localhost", 333)
    octave_config.set_calibration_db(os.path.dirname(__file__))
    octave_mock = MagicMock()
    monkeypatch.setattr(f"qm.octave.octave_config.Octave", octave_mock)

    qmm = QuantumMachinesManager(**host_port, octave=octave_config)

    qm = qmm.open_qm(config)
    first_config = qm.get_config()
    qm.octave.set_element_parameters_from_calibration_db("qe2")
    second_config = qm.get_config()
    assert first_config == second_config
