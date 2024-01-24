import functools
import itertools

import pytest
from marshmallow import ValidationError

from qm.exceptions import ConfigValidationException, NoInputsOrOutputsError
from qm.api.models.capabilities import ServerCapabilities
from qm.grpc.qua_config import QuaConfigOutputPulseParametersPolarity
from qm.program._qua_config_schema import (
    ElementSchema,
    QuaConfigSchema,
    ControllerSchema,
    validate_config_capabilities,
)
from tests.conftest import ignore_warnings_context

_POSSIBLE_INPUTS = [
    {
        "multipleInputs": {
            "inputs": {
                "port1": ("con1", 1),
                "port2": ("con1", 2),
            }
        }
    },
    {
        "mixInputs": {
            "I": ("con1", 1),
            "Q": ("con1", 2),
            "mixer": "mixer",
            "lo_frequency": 1e6,
        }
    },
    {"singleInput": {"port": ("con1", 1)}},
    {"singleInputCollection": {"inputs": {"o1": ("con1", 3), "o2": ("con1", 4)}}},
]


def _create_server_capabilities(
    *,
    has_job_streaming_state=False,
    supports_multiple_inputs_for_element=False,
    supports_analog_delay=False,
    supports_shared_oscillators=False,
    supports_crosstalk=False,
    supports_shared_ports=False,
    supports_input_stream=False,
    supports_new_grpc_structure=False,
    supports_double_frequency=False,
    supports_command_timestamps=False,
    supports_inverted_digital_output=False,
    supports_sticky_elements=False,
    supports_octave_reset=False,
    supports_fast_frame_rotation=False,
) -> ServerCapabilities:
    return ServerCapabilities(
        has_job_streaming_state=has_job_streaming_state,
        supports_multiple_inputs_for_element=supports_multiple_inputs_for_element,
        supports_analog_delay=supports_analog_delay,
        supports_shared_oscillators=supports_shared_oscillators,
        supports_crosstalk=supports_crosstalk,
        supports_shared_ports=supports_shared_ports,
        supports_input_stream=supports_input_stream,
        supports_new_grpc_structure=supports_new_grpc_structure,
        supports_double_frequency=supports_double_frequency,
        supports_command_timestamps=supports_command_timestamps,
        supports_inverted_digital_output=supports_inverted_digital_output,
        supports_sticky_elements=supports_sticky_elements,
        supports_octave_reset=supports_octave_reset,
        supports_fast_frame_rotation=supports_fast_frame_rotation,
        fem_number_in_simulator=0,
    )


def test_element_with_no_inputs_no_outputs():
    conf = {
        "version": "1",
        "elements": {
            "el1": {
                "intermediate_frequency": 100e6,
                "outputs": {},
            }
        },
    }
    with pytest.raises(NoInputsOrOutputsError):
        QuaConfigSchema().load(conf)


@pytest.mark.parametrize("two_elements", itertools.permutations(_POSSIBLE_INPUTS, r=2))
def test_valid_multiple_inputs(two_elements):
    a, b = two_elements
    _valid_config = {
        "intermediate_frequency": 100e6,
        "outputs": {
            "out1": ("con1", 1),
            "out2": ("con1", 2),
        },
        "time_of_flight": 192,
        "smearing": 0,
    }

    def conf(*args):
        return {
            "version": "1",
            "elements": {
                "el1": {
                    **_valid_config,
                    **functools.reduce(lambda x, y: ({**x, **y}), args),
                }
            },
        }

    # make sure we can load each
    QuaConfigSchema().load(conf(a))
    QuaConfigSchema().load(conf(b))
    with pytest.raises(ValidationError, match="Can't support more than a single input type"):
        QuaConfigSchema().load(conf(a, b))


class TestElementWithMultipleInputs:
    _valid_config = {
        "multipleInputs": {
            "inputs": {
                "port1": ("con1", 1),
                "port2": ("con1", 2),
            }
        },
        "intermediate_frequency": 100e6,
        "outputs": {
            "out1": ("con1", 1),
            "out2": ("con1", 2),
        },
        "time_of_flight": 192,
        "smearing": 0,
    }

    def test_valid_multiple_inputs(self):
        schema = ElementSchema()
        schema.load(self._valid_config)

    def test_qua_config_fail_if_no_capability(self):
        schema = QuaConfigSchema()
        conf = schema.load({"version": "1", "elements": {"el1": self._valid_config}})
        with pytest.raises(
            ConfigValidationException,
            match="Server does not support multiple inputs for elements",
        ):
            validate_config_capabilities(conf, _create_server_capabilities(has_job_streaming_state=True))

    def test_qua_config_pass_if_no_capability(self):
        schema = QuaConfigSchema()
        conf = schema.load({"version": "1", "elements": {"el1": self._valid_config}})
        validate_config_capabilities(
            conf,
            _create_server_capabilities(
                has_job_streaming_state=True,
                supports_multiple_inputs_for_element=True,
            ),
        )


class TestPortWithAnalogDelay:
    _valid_config = {"type": "opx1", "analog_outputs": {1: {"offset": 0.0, "delay": 5}}}

    def test_valid_analog_delay(self):
        schema = ControllerSchema()
        schema.load(self._valid_config)

    def test_qua_config_fail_if_no_capability(self):
        schema = QuaConfigSchema()
        conf = schema.load({"version": "1", "controllers": {"con1": self._valid_config}})
        with pytest.raises(
            ConfigValidationException,
            match="Server does not support analog delay used in controller",
        ):
            validate_config_capabilities(
                conf,
                _create_server_capabilities(
                    has_job_streaming_state=True,
                ),
            )

    def test_qua_config_pass_if_capability(self):
        schema = QuaConfigSchema()
        conf = schema.load({"version": "1", "controllers": {"con1": self._valid_config}})
        validate_config_capabilities(
            conf,
            _create_server_capabilities(
                has_job_streaming_state=True,
                supports_analog_delay=True,
            ),
        )


class TestElementWithOutput:
    def test_all_good(self):
        schema = ElementSchema()
        schema.load(
            {
                "singleInput": {
                    "port": ("con1", 1),
                },
                "intermediate_frequency": 100e6,
                "outputs": {
                    "out1": ("con1", 1),
                    "out2": ("con1", 2),
                },
                "time_of_flight": 192,
                "smearing": 0,
            }
        )

    def test_all_good_empty_outputs(self):
        schema = ElementSchema()
        schema.load(
            {
                "singleInput": {
                    "port": ("con1", 1),
                },
                "intermediate_frequency": 100e6,
                "outputs": {},
            }
        )

    def test_have_tof(self):
        schema = ElementSchema()
        with pytest.raises(ValidationError, match="must have time_of_flight"):
            schema.load(
                {
                    "singleInput": {
                        "port": ("con1", 1),
                    },
                    "intermediate_frequency": 100e6,
                    "outputs": {
                        "out1": ("con1", 1),
                        "out2": ("con1", 2),
                    },
                    # 'time_of_flight': 192,
                    "smearing": 0,
                }
            )

    def test_have_smearing(self):
        schema = ElementSchema()
        with pytest.raises(ValidationError, match="must have smearing"):
            schema.load(
                {
                    "singleInput": {
                        "port": ("con1", 1),
                    },
                    "intermediate_frequency": 100e6,
                    "outputs": {
                        "out1": ("con1", 1),
                        "out2": ("con1", 2),
                    },
                    "time_of_flight": 192,
                    # 'smearing': 0,
                }
            )

    def test_no_output_nothing_required(self):
        schema = ElementSchema()
        schema.load(
            {
                "singleInput": {
                    "port": ("con1", 1),
                },
                "intermediate_frequency": 100e6,
                # 'outputs': {
                #     'out1': ('con1', 1),
                #     'out2': ('con1', 2),
                # },
                # 'time_of_flight': 192,
                # 'smearing': 0,
            }
        )

    def test_no_output_should_not_have_tof(self):
        schema = ElementSchema()
        with pytest.raises(
            ValidationError,
            match="time_of_flight should be used only with elements that have outputs",
        ):
            schema.load(
                {
                    "singleInput": {
                        "port": ("con1", 1),
                    },
                    "intermediate_frequency": 100e6,
                    # 'outputs': {
                    #     'out1': ('con1', 1),
                    #     'out2': ('con1', 2),
                    # },
                    "time_of_flight": 192,
                    # 'smearing': 0,
                }
            )

    def test_no_output_should_not_have_smearing(self):
        schema = ElementSchema()
        with pytest.raises(
            ValidationError,
            match="smearing should be used only with elements that have outputs",
        ):
            schema.load(
                {
                    "singleInput": {
                        "port": ("con1", 1),
                    },
                    "intermediate_frequency": 100e6,
                    # 'outputs': {
                    #     'out1': ('con1', 1),
                    #     'out2': ('con1', 2),
                    # },
                    # 'time_of_flight': 192,
                    "smearing": 0,
                }
            )


class TestElementWithSharedOscillator:
    _valid_config = {"singleInput": {"port": ("con1", 1)}, "oscillator": "osc"}

    def test_valid_multiple_inputs(self):
        schema = ElementSchema()
        schema.load(self._valid_config)

    def test_qua_config_fail_if_no_capability(self):
        schema = QuaConfigSchema()
        conf = schema.load({"version": "1", "elements": {"el1": self._valid_config}})
        with pytest.raises(
            ConfigValidationException,
            match="Server does not support shared oscillators for elements used",
        ):
            validate_config_capabilities(
                conf,
                _create_server_capabilities(
                    has_job_streaming_state=True,
                ),
            )

    def test_qua_config_pass_if_no_capability(self):
        schema = QuaConfigSchema()
        conf = schema.load({"version": "1", "elements": {"el1": self._valid_config}})
        validate_config_capabilities(
            conf,
            _create_server_capabilities(
                has_job_streaming_state=True,
                supports_shared_oscillators=True,
            ),
        )


class TestElementWithOutputPulseParameters:
    _basic_config = {
        "singleInput": {
            "port": ("con1", 1),
        },
        "intermediate_frequency": 100e6,
        "outputs": {
            "out1": ("con1", 1),
        },
        "time_of_flight": 192,
        "smearing": 0,
    }

    def test_no_parameters(self):
        schema = ElementSchema()
        schema.load(self._basic_config)

    def test_all_parameters(self):
        schema = ElementSchema()
        output_pulse_parameters = {
            "signalThreshold": 800,
            "signalPolarity": "Ascending",
            "derivativeThreshold": 300,
            "derivativePolarity": "Descending",
        }
        self._basic_config["outputPulseParameters"] = output_pulse_parameters
        loaded = schema.load(self._basic_config)
        assert loaded.output_pulse_parameters.signal_polarity == QuaConfigOutputPulseParametersPolarity.ASCENDING
        assert loaded.output_pulse_parameters.derivative_polarity == QuaConfigOutputPulseParametersPolarity.DESCENDING

        output_pulse_parameters = {
            "signalThreshold": 800,
            "signalPolarity": "Descending",
            "derivativeThreshold": 300,
            "derivativePolarity": "Ascending",
        }
        self._basic_config["outputPulseParameters"] = output_pulse_parameters
        loaded = schema.load(self._basic_config)
        assert loaded.output_pulse_parameters.signal_polarity == QuaConfigOutputPulseParametersPolarity.DESCENDING
        assert loaded.output_pulse_parameters.derivative_polarity == QuaConfigOutputPulseParametersPolarity.ASCENDING

    def test_all_new_parameters(self):
        schema = ElementSchema()
        output_pulse_parameters = {
            "signalThreshold": 800,
            "signalPolarity": "Above",
            "derivativeThreshold": 300,
            "derivativePolarity": "Below",
        }
        self._basic_config["outputPulseParameters"] = output_pulse_parameters
        loaded = schema.load(self._basic_config)
        assert loaded.output_pulse_parameters.signal_polarity == QuaConfigOutputPulseParametersPolarity.ASCENDING
        assert loaded.output_pulse_parameters.derivative_polarity == QuaConfigOutputPulseParametersPolarity.DESCENDING

        output_pulse_parameters = {
            "signalThreshold": 800,
            "signalPolarity": "Below",
            "derivativeThreshold": 300,
            "derivativePolarity": "Above",
        }
        self._basic_config["outputPulseParameters"] = output_pulse_parameters
        loaded = schema.load(self._basic_config)
        assert loaded.output_pulse_parameters.signal_polarity == QuaConfigOutputPulseParametersPolarity.DESCENDING
        assert loaded.output_pulse_parameters.derivative_polarity == QuaConfigOutputPulseParametersPolarity.ASCENDING

    def test_invalid_missing_one(self):
        schema = ElementSchema()
        output_pulse_parameters = {
            "signalThreshold": 800,
            "signalPolarity": "Above",
            "derivativeThreshold": 300,
        }
        self._basic_config["outputPulseParameters"] = output_pulse_parameters
        with pytest.raises(
            ConfigValidationException,
            match="An element defining the output pulse parameters",
        ):
            schema.load(self._basic_config)

    def test_invalid_missing_two(self):
        schema = ElementSchema()
        output_pulse_parameters = {
            "signalThreshold": 800,
            "derivativeThreshold": 300,
        }
        self._basic_config["outputPulseParameters"] = output_pulse_parameters
        with pytest.raises(
            ConfigValidationException,
            match="An element defining the output pulse parameters",
        ):
            schema.load(self._basic_config)

    def test_all_invalid_signal_polairty(self):
        schema = ElementSchema()
        output_pulse_parameters = {
            "signalThreshold": 800,
            "signalPolarity": "Rising",
            "derivativeThreshold": 300,
            "derivativePolarity": "Below",
        }
        self._basic_config["outputPulseParameters"] = output_pulse_parameters
        with pytest.raises(ConfigValidationException, match="but it must be one of"):
            schema.load(self._basic_config)

    def test_all_invalid_derivative_polairty(self):
        schema = ElementSchema()
        output_pulse_parameters = {
            "signalThreshold": 800,
            "signalPolarity": "Rising",
            "derivativeThreshold": 300,
            "derivativePolarity": "Falling",
        }
        self._basic_config["outputPulseParameters"] = output_pulse_parameters
        with pytest.raises(ConfigValidationException, match="but it must be one of"):
            schema.load(self._basic_config)


class TestPortWithCrosstalk:
    _valid_config = {"type": "opx1", "analog_outputs": {1: {"offset": 0.0, "crosstalk": {1: 0.2, 2: 0.3}}}}

    def test_valid_crosstalk(self):
        schema = ControllerSchema()
        schema.load(self._valid_config)

    def test_qua_config_fail_if_no_capability(self):
        schema = QuaConfigSchema()
        conf = schema.load({"version": "1", "controllers": {"con1": self._valid_config}})
        with pytest.raises(
            ConfigValidationException,
            match="Server does not support channel weights used in controller",
        ):
            validate_config_capabilities(
                conf,
                _create_server_capabilities(
                    has_job_streaming_state=True,
                ),
            )

    def test_qua_config_pass_if_capability(self):
        schema = QuaConfigSchema()
        conf = schema.load({"version": "1", "controllers": {"con1": self._valid_config}})
        validate_config_capabilities(
            conf,
            _create_server_capabilities(
                has_job_streaming_state=True,
                supports_crosstalk=True,
                supports_shared_ports=False,
                supports_input_stream=False,
            ),
        )


class TestElementWithDoubleIntermediateFreq:
    _single_element = {
        "singleInput": {
            "port": ("con1", 1),
        },
        "intermediate_frequency": 10000.1,
    }
    _elements = {
        "readout_res": {
            "mixInputs": {"I": ("con1", 5), "Q": ("con1", 6), "lo_frequency": 6.1423e9, "mixer": "mxr_rr"},
            "intermediate_frequency": 12e6,
            "operations": {"pulse1": "pulse1_in", "ro_pulse": "meas_pulse_in", "ro_pulse_long": "long_meas_pulse_in"},
            "time_of_flight": 200,
            "smearing": 0,
            "outputs": {"out1": ("con1", 1), "out2": ("con1", 2)},
        },
        "qe_iq_ref": {
            "mixInputs": {"I": ("con1", 1), "Q": ("con1", 2), "lo_frequency": 0.0, "mixer": "mxr1"},
            "intermediate_frequency": 0.0,
            "operations": {"pulse1": "pulse1_iq_in", "pulse_long": "pulse_long_iq_in", "ramp": "ramp_arb"},
        },
        "qe_iq1": {
            "mixInputs": {
                "I": ("con1", 3),
                "Q": ("con1", 4),
            },
            "intermediate_frequency": 0.0,
            "operations": {
                "pulse1": "pulse1_iq_in",
            },
        },
        "qe1": {
            "singleInput": {"port": ("con1", 5)},
            "intermediate_frequency": 0.0,
            "operations": {
                "pulse1": "pulse1_in",
                "pulse_long": "pulse_long_in",
                "pulse_tiny": "tiny_pulse_in",
                "pulse_short": "pulse_short_in",
                "pulse_arb": "pulse_arb",
                "gaussian": "gaussian_in",
            },
            "outputs": {"out1": ["con1", 2]},
            "time_of_flight": 0,
            "smearing": 0,
        },
        "qe2": {
            "singleInput": {"port": ("con1", 6)},
            "intermediate_frequency": 0.0,
            "operations": {"pulse1": "pulse1_in", "pulse_long": "pulse_long_in", "pulse_short": "pulse_short_in"},
        },
        "qe3": {
            "singleInput": {"port": ("con1", 7)},
            "intermediate_frequency": 0.0,
            "operations": {"pulse_long": "pulse_long_in", "pulse1": "pulse1_in"},
        },
    }

    def test_element_schema_with_int_freq(self):
        schema = ElementSchema()
        self._single_element["intermediate_frequency"] = 10000
        conf = schema.load(self._single_element)
        intermediate_frequency = conf.intermediate_frequency_double
        assert intermediate_frequency == self._single_element["intermediate_frequency"]
        assert isinstance(intermediate_frequency, float)

    def test_element_schema_with_float_freq(self):
        schema = ElementSchema()
        conf = schema.load(self._single_element)
        intermediate_frequency = conf.intermediate_frequency_double
        assert intermediate_frequency == self._single_element["intermediate_frequency"]
        assert isinstance(intermediate_frequency, float)

    @pytest.mark.parametrize("element", argvalues=list(_elements.values()), ids=list(_elements.keys()))
    def test_many_elements_schema_with_float_freq(self, element: dict, capability_container):
        with ignore_warnings_context():
            capability_container.capabilities.override(
                ServerCapabilities(
                    True, True, True, True, True, True, True, True, False, True, True, True, True, True, 0
                )
            )
            schema = ElementSchema()
            conf = schema.load(element)
            intermediate_frequency_int = conf.intermediate_frequency
            assert intermediate_frequency_int == int(element["intermediate_frequency"])
            assert isinstance(intermediate_frequency_int, int)

            capability_container.capabilities.override(
                ServerCapabilities(
                    True, True, True, True, True, True, True, True, True, True, True, True, True, True, 0
                )
            )
            schema = ElementSchema()
            conf = schema.load(element)
            intermediate_frequency = conf.intermediate_frequency_double
            assert intermediate_frequency == element["intermediate_frequency"]
            assert isinstance(intermediate_frequency, float)


class TestElementWithSticky:
    _single_element = {
        "singleInput": {
            "port": ("con1", 1),
        },
        "sticky": {"analog": True, "duration": 16, "digital": True},
    }

    def test_element_scheme_with_sticky(self, capability_container):
        with ignore_warnings_context():
            capability_container.capabilities.override(
                ServerCapabilities(
                    True, True, True, True, True, True, True, True, True, True, True, True, True, True, 0
                )
            )
            schema = ElementSchema()
            conf = schema.load(self._single_element)
            sticky = conf.sticky
            assert sticky.duration == int(self._single_element["sticky"]["duration"] / 4)
            assert sticky.analog == self._single_element["sticky"]["analog"]
            assert sticky.digital == self._single_element["sticky"]["digital"]

    def test_element_scheme_sticky_without_capabilities(self, capability_container):
        with ignore_warnings_context():
            capability_container.capabilities.override(
                ServerCapabilities(
                    True, True, True, True, True, True, True, True, True, True, True, True, False, True, 0
                )
            )
            self._single_element["sticky"] = {"analog": True, "duration": 16}
            schema = ElementSchema()
            conf = schema.load(self._single_element)
            hold_offset = conf.hold_offset
            assert hold_offset.duration == self._single_element["sticky"]["duration"] // 4
