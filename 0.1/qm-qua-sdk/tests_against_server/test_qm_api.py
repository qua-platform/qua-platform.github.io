from copy import deepcopy

import pytest
from _pytest.logging import LogCaptureFixture

from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager

config = {
    "version": 1,
    "controllers": {
        "con1": {
            "analog_outputs": {f"{i}": {"offset": 0.0} for i in range(1, 11)},
            "digital_outputs": {f"{i}": {} for i in range(1, 11)},
            "digital_inputs": {
                1: {"threshold": 0.1, "polarity": "RISING", "deadtime": 4},
                2: {"threshold": 0.1, "polarity": "RISING", "deadtime": 4}}
        },
    },
    "elements": {
        "oneq_0_ha": {
            "intermediate_frequency": 102268000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con1", 7)},
        },

    },
    "pulses": {
        "empty_pulse": {
            "operation": "control",
            "length": 100,
            "waveforms": {"single": "zero_wf"},
        },
        "SquarePulse_a": {
            "operation": "control",
            "length": 5700,
            "waveforms": {"single": "SquarePulse_a"},
        },
    },
    "waveforms": {
        "zero_wf": {"type": "constant", "sample": 0.0},
        "SquarePulse_a": {"type": "constant", "sample": 0.25},  # 0.03201666232864798},
    },
}

pytestmark = pytest.mark.only_qop2


def get_qm(host_info):
    qmm = QuantumMachinesManager(**host_info)
    qm = qmm.open_qm(config)
    return qm


@pytest.mark.parametrize("freq_type", [int, float])
def test_returned_frequencies_type_is_correct(host_port, freq_type):
    new_config = deepcopy(config)
    lo_freq = 100.0
    intermediate_frequency = 111.0
    new_config["elements"]["new_element"] = {
        "intermediate_frequency": freq_type(intermediate_frequency),
        "mixInputs": {
            "I": ("con1", 1),
            "Q": ("con1", 2),
            "lo_frequency": freq_type(lo_freq),
        },
    }
    new_config["controllers"]["con1"]["digital_inputs"] = {}
    qmm = QuantumMachinesManager(**host_port)
    qm = qmm.open_qm(new_config)
    returned_config = qm.get_config()
    assert isinstance(
        returned_config["elements"]["new_element"]["mixInputs"]["lo_frequency"], float)
    assert isinstance(
        returned_config["elements"]["new_element"]["intermediate_frequency"], float)


def test_raise_warning_when_using_old_gateway_with_float_freq(host_port,
                                                              caplog: LogCaptureFixture):
    new_config = deepcopy(config)
    frequency_types = ["intermediate_frequency", "lo_frequency"]
    lo_freq = 100.5
    intermediate_frequency = 111.5
    element_name = "new_element"
    new_config["elements"][element_name] = {
        frequency_types[0]: intermediate_frequency,
        "mixInputs": {
            "I": ("con1", 1),
            "Q": ("con1", 2),
            frequency_types[1]: lo_freq,
        },
    }
    new_config["controllers"]["con1"]["digital_inputs"] = {}
    qmm = QuantumMachinesManager(**host_port)
    qmm.open_qm(new_config)
    messages = [
        x.message for x in caplog.records if x.levelno == logging.WARNING
    ]
    warning_message_prefix = "Server does not support float frequency."
    for message in messages:
        assert message.startswith(warning_message_prefix)


def test_rounding_on_old_gateway(host_port):
    new_config = deepcopy(config)
    frequency_types = ["intermediate_frequency", "lo_frequency"]
    lo_freq = 100.5
    intermediate_frequency = 111.5
    element_name = "new_element"
    new_config["elements"][element_name] = {
        frequency_types[0]: intermediate_frequency,
        "mixInputs": {
            "I": ("con1", 1),
            "Q": ("con1", 2),
            frequency_types[1]: lo_freq,
        },
    }
    new_config["controllers"]["con1"]["digital_inputs"] = {}
    qmm = QuantumMachinesManager(**host_port)
    qm = qmm.open_qm(new_config)
    returned_config = qm.get_config()
    if not qmm._caps.supports_double_frequency:
        assert returned_config["elements"][element_name]["mixInputs"]["lo_frequency"] == int(lo_freq)
        assert returned_config["elements"][element_name]["intermediate_frequency"] == int(intermediate_frequency)
    else:
        assert returned_config["elements"][element_name]["mixInputs"]["lo_frequency"] == lo_freq
        assert returned_config["elements"][element_name]["intermediate_frequency"] == intermediate_frequency


class TestOPDApi:

    def _test_get_and_set_digital_input_property(self, host_port, port, property_name,
                                                 value_to_set):
        qm = get_qm(host_port)
        qm.__getattribute__(f"set_digital_input_{property_name}")(port, value_to_set)
        qm_stored_value = qm.__getattribute__(f"get_digital_input_{property_name}")(
            port)
        assert qm_stored_value == value_to_set
        return

    @pytest.mark.parametrize("port", [1, 2])
    @pytest.mark.parametrize("deadtime_value", [4, 8, 15])
    def test_set_and_get_digital_input_deadtime(self, host_port, port, deadtime_value):
        self._test_get_and_set_digital_input_property(host_port, ("con1", port),
                                                      "deadtime", deadtime_value)

    @pytest.mark.parametrize("port", [1, 2])
    @pytest.mark.parametrize("polarity_value", ["RISING", "FALLING"])
    def test_set_and_get_digital_input_polarity(self, host_port, port, polarity_value):
        self._test_get_and_set_digital_input_property(host_port, ("con1", port),
                                                      "polarity", polarity_value)

    @pytest.mark.parametrize("port", [1, 2])
    @pytest.mark.parametrize("threshold_value", [0.2, 0.9, 2.5, 3.0])
    def test_set_and_get_digital_input_threshold(self, host_port, port,
                                                 threshold_value):
        self._test_get_and_set_digital_input_property(host_port, ("con1", port),
                                                      "threshold", threshold_value)

    @pytest.mark.parametrize("port", [1, 2])
    @pytest.mark.parametrize("deadtime_value", [0, 3, 17, 18])
    def test_set_invalid_deadtime_values(self, host_port, port, deadtime_value):
        qm = get_qm(host_port)
        with pytest.raises(BaseException):
            qm.set_digital_input_deadtime(("con1", port), deadtime_value)

    @pytest.mark.parametrize("port", [1, 2])
    @pytest.mark.parametrize("polarity_value", [0, 1, "0", "1", "HIGH", "LOW"])
    def test_set_invalid_polarity_values(self, host_port, port, polarity_value):
        qm = get_qm(host_port)
        with pytest.raises((BaseException)):
            qm.set_digital_input_polarity(("con1", port), polarity_value)

    @pytest.mark.parametrize("port", [1, 2])
    @pytest.mark.parametrize("threshold_value", [-0.2, -0.0001, 3.3])
    def test_set_invalid_threshold_values(self, host_port, port, threshold_value):
        qm = get_qm(host_port)
        with pytest.raises(BaseException):
            qm.set_digital_input_threshold(("con1", port), threshold_value)

    def _test_value_remains_the_same_after_execution(self, host_port, port,
                                                     property_name, value_to_set):
        with program() as p:
            a = declare(int)
            save(a, "a")

        qm = get_qm(host_port)
        qm.__getattribute__(f"set_digital_input_{property_name}")(port, value_to_set)
        qm.execute(p)
        qm_stored_value = qm.__getattribute__(f"get_digital_input_{property_name}")(
            port)
        assert qm_stored_value == value_to_set

    @pytest.mark.parametrize("port", [1, 2])
    @pytest.mark.parametrize("deadtime_value", [4, 8, 15])
    def test_deadtime_remains_the_same_after_execution(self, host_port, port,
                                                       deadtime_value):
        self._test_value_remains_the_same_after_execution(host_port, ("con1", port),
                                                          "deadtime", deadtime_value)

    @pytest.mark.parametrize("port", [1, 2])
    @pytest.mark.parametrize("polarity_value", ["RISING", "FALLING"])
    def test_polarity_remains_the_same_after_execution(self, host_port, port,
                                                       polarity_value):
        self._test_value_remains_the_same_after_execution(host_port, ("con1", port),
                                                          "polarity", polarity_value)

    @pytest.mark.parametrize("port", [1, 2])
    @pytest.mark.parametrize("threshold_value", [0.2, 0.9, 2.5, 3.0])
    def test_threshold_remains_the_same_after_execution(self, host_port, port,
                                                        threshold_value):
        self._test_value_remains_the_same_after_execution(host_port, ("con1", port),
                                                          "threshold", threshold_value)
