import pytest

from qm.exceptions import ConfigValidationException
from qm.api.models.capabilities import ServerCapabilities
from qm.program._qua_config_schema import (
    QuaConfigSchema,
    validate_config_capabilities,
)


class TestControllerWithSharedPorts:
    config_with_shareable = {
        "version": 1,
        "controllers": {
            "con1": {
                "type": "opx1",
                "analog_outputs": {
                    1: {"offset": 0.1, "shareable": True},
                    2: {"offset": 0.1},
                },
            }
        },
    }
    config_without_shareable = {
        "version": 1,
        "controllers": {
            "con1": {
                "type": "opx1",
                "analog_outputs": {
                    1: {"offset": 0.1},
                    2: {"offset": 0.1},
                },
            }
        },
    }

    def test_qua_config_fail_if_no_capability(self):
        schema = QuaConfigSchema()
        conf = schema.load(self.config_with_shareable)
        with pytest.raises(
            ConfigValidationException, match="Server does not support shareable ports"
        ):
            validate_config_capabilities(
                conf,
                ServerCapabilities(
                    has_job_streaming_state=True,
                    supports_multiple_inputs_for_element=False,
                    supports_analog_delay=False,
                    supports_shared_oscillators=False,
                    supports_crosstalk=False,
                    supports_shared_ports=False,
                    supports_input_stream=False,
                    supports_double_frequency=False,
                    supports_command_timestamps=False,
                    supports_new_grpc_structure=False,
                    supports_sticky_elements=False,
                    supports_octave_reset=False,
                ),
            )

    def test_qua_config_pass_if_no_capability(self):
        schema = QuaConfigSchema()
        conf = schema.load(self.config_without_shareable)
        validate_config_capabilities(
            conf,
            ServerCapabilities(
                has_job_streaming_state=True,
                supports_multiple_inputs_for_element=False,
                supports_analog_delay=False,
                supports_shared_oscillators=False,
                supports_crosstalk=False,
                supports_shared_ports=False,
                supports_input_stream=False,
                supports_double_frequency=False,
                supports_command_timestamps=False,
                supports_new_grpc_structure=False,
                supports_sticky_elements=False,
                supports_octave_reset=False,
            ),
        )

    def test_qua_config_pass_if_has_capability(self):
        schema = QuaConfigSchema()
        conf = schema.load(self.config_with_shareable)
        validate_config_capabilities(
            conf,
            ServerCapabilities(
                has_job_streaming_state=True,
                supports_multiple_inputs_for_element=False,
                supports_analog_delay=False,
                supports_shared_oscillators=False,
                supports_crosstalk=False,
                supports_shared_ports=True,
                supports_input_stream=False,
                supports_new_grpc_structure=False,
                supports_double_frequency=False,
                supports_command_timestamps=False,
                supports_sticky_elements=False,
                supports_octave_reset=False,
            ),
        )

    def test_qua_config_shareable_default_value_is_false(self):
        schema = QuaConfigSchema()
        conf = schema.load(self.config_with_shareable)
        assert conf.v1_beta.controllers["con1"].analog_outputs[2].shareable is False
