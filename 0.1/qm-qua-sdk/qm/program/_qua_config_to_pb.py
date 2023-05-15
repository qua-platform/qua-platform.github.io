from typing import Any, Dict, List, Union, Optional

import numpy as np
from betterproto.lib.google.protobuf import Empty
from dependency_injector.wiring import Provide, inject

from qm.grpc import qua_config, octave_models
from qm.exceptions import ConfigValidationException
from qm.api.models.capabilities import ServerCapabilities
from qm.containers.capabilities_container import CapabilitiesContainer
from qm.program._validate_config_schema import (
    validate_oscillator,
    validate_output_tof,
    validate_used_inputs,
    validate_output_smearing,
    validate_arbitrary_waveform,
    validate_timetagging_parameters,
)


class OctaveConnectionAmbiguity(Exception):
    def __str__(self):
        return (
            "It is not allowed to override the default connection of the Octave. You should either state the "
            "default connection to Octave in the controller level, or set each port separately in the port level."
        )


def octave_connection_to_pb(
    connection_type: str,
    *,
    device_name: Optional[str] = None,
    port_num: Optional[int] = None,
    port_data: Optional[dict] = None,
) -> Optional[Union[octave_models.OctaveIfInputPort, octave_models.OctaveIfOutputPort]]:
    if connection_type == "input":
        return_class, port_class = (
            octave_models.OctaveIfInputPort,
            octave_models.OctaveIfInputPortName,
        )
    elif connection_type == "output":
        return_class, port_class = (
            octave_models.OctaveIfOutputPort,
            octave_models.OctaveIfOutputPortName,
        )
    elif connection_type == "digital_input":
        return_class, port_class = (
            octave_models.OctaveDigitalInputPort,
            octave_models.OctaveDigitalInputPortName,
        )
    elif connection_type == "digital_output":
        return_class, port_class = (
            octave_models.OctaveDigitalOutputPort,
            octave_models.OctaveDigitalOutputPortName,
        )
    else:
        raise ConfigValidationException("Unknown connection type")

    if device_name is not None:
        if isinstance(port_data, dict) and port_data.get("connectivity") is not None:
            raise OctaveConnectionAmbiguity
        port = port_class(port_num - 1)
        # The enum is 0-based and the port enumeration is 1-based, so we need to align them.
        return return_class(device_name=device_name, port_name=port)

    connectivity = port_data.get("connectivity")
    if connectivity is None:
        return None

    device_name, port_name = connectivity
    port = port_class[port_name]
    return return_class(device_name=device_name, port_name=port)


def analog_input_port_to_pb(
    data: Dict[str, Any],
    octave_output: Optional[octave_models.OctaveIfOutputPort],
) -> qua_config.QuaConfigAnalogInputPortDec:
    analog_input = qua_config.QuaConfigAnalogInputPortDec(
        offset=data.get("offset", 0.0),
        shareable=bool(data.get("shareable")),
        gain_db=int(data.get("gain_db", 0)),
    )

    if octave_output is not None:
        analog_input.octave_connectivity = octave_output

    return analog_input


def analog_output_port_to_pb(
    data: Dict[str, Any], octave_input: Optional[octave_models.OctaveIfInputPort]
) -> qua_config.QuaConfigAnalogOutputPortDec:
    analog_output = qua_config.QuaConfigAnalogOutputPortDec(shareable=bool(data.get("shareable")))

    if octave_input is not None:
        analog_output.octave_connectivity = octave_input

    if "offset" in data:
        analog_output.offset = data["offset"]

    if "delay" in data:
        delay = data.get("delay", 0)
        if delay < 0:
            raise ConfigValidationException(f"analog output delay cannot be a negative value, given value: {delay}")
        analog_output.delay = delay

    if "filter" in data:
        analog_output.filter = qua_config.QuaConfigAnalogOutputPortFilter(
            feedforward=data["filter"]["feedforward"],
            feedback=data["filter"]["feedback"],
        )

    if "crosstalk" in data:
        for k, v in data["crosstalk"].items():
            analog_output.crosstalk[int(k)] = v

    return analog_output


def digital_output_port_to_pb(data: Dict[str, Any]) -> qua_config.QuaConfigDigitalOutputPortDec:
    digital_output = qua_config.QuaConfigDigitalOutputPortDec(
        shareable=bool(data.get("shareable")),
        inverted=bool(data.get("inverted", False)),
    )
    # TODO - once we decide how to add digital connectivity this can be added back
    # if "connectivity" in data:
    #     digital_output.octave_connectivity = octave_connection_to_pb("digital_input", port_data=data)
    return digital_output


def digital_input_port_to_pb(data: Dict):
    digital_input = qua_config.QuaConfigDigitalInputPortDec(shareable=bool(data.get("shareable")))

    if "window" in data:
        digital_input.window = data["window"]

    if "threshold" in data:
        digital_input.threshold = data["threshold"]

    if "polarity" in data:
        if data["polarity"].upper() == "RISING":
            digital_input.polarity = qua_config.QuaConfigDigitalInputPortDecPolarity.RISING
        elif data["polarity"].upper() == "FALLING":
            digital_input.polarity = qua_config.QuaConfigDigitalInputPortDecPolarity.FALLING

    if "deadtime" in data:
        digital_input.deadtime = int(data["deadtime"])

    # TODO - once we decide how to add digital connectivity this can be added back
    # if "connectivity" in data:
    #     digital_input.octave_connectivity = octave_connection_to_pb("digital_output", port_data=data)

    return digital_input


def controller_to_pb(data: Dict[str, Any]) -> qua_config.QuaConfigControllerDec:
    cont = qua_config.QuaConfigControllerDec(type=data.get("type", "opx1"))

    if "type" in data:
        cont.type = data["type"]

    connected_octave_name = data.get("connectivity")
    if "analog_outputs" in data:
        for _k, _v in data["analog_outputs"].items():
            int_k = int(_k)
            octave_input = octave_connection_to_pb(
                "input", device_name=connected_octave_name, port_num=int_k, port_data=_v
            )
            cont.analog_outputs[int_k] = analog_output_port_to_pb(_v, octave_input)

    if "analog_inputs" in data:
        for _k, _v in data["analog_inputs"].items():
            int_k = int(_k)
            octave_input = octave_connection_to_pb(
                "output",
                device_name=connected_octave_name,
                port_num=int_k,
                port_data=_v,
            )
            cont.analog_inputs[int(_k)] = analog_input_port_to_pb(_v, octave_input)

    if "digital_outputs" in data:
        for _k, _v in data["digital_outputs"].items():
            cont.digital_outputs[int(_k)] = digital_output_port_to_pb(_v)

    if "digital_inputs" in data:
        for _k, _v in data["digital_inputs"].items():
            cont.digital_inputs[int(_k)] = digital_input_port_to_pb(_v)

    return cont


def get_octave_loopbacks(data: List) -> List[octave_models.OctaveLoopback]:
    loopbacks = [
        octave_models.OctaveLoopback(
            lo_source_input=octave_models.OctaveLoSourceInput[loopback[1]],
            lo_source_generator=octave_models.OctaveSynthesizerPort(
                device_name=loopback[0][0],
                port_name=octave_models.OctaveSynthesizerOutputName[loopback[0][1]],
            ),
        )
        for loopback in data
    ]
    return loopbacks


def octave_to_pb(data: Dict[str, Any]) -> octave_models.OctaveConfig:
    loopbacks = get_octave_loopbacks(data["loopbacks"])
    return octave_models.OctaveConfig(loopbacks)


@inject
def mixer_ref_to_pb(
    name: str,
    lo_frequency: int,
    capabilities: ServerCapabilities = Provide[CapabilitiesContainer.capabilities],
) -> qua_config.QuaConfigMixerRef:
    item = qua_config.QuaConfigMixerRef(mixer=name, lo_frequency=int(lo_frequency))
    if capabilities.supports_double_frequency:
        item.lo_frequency_double = float(lo_frequency)
    return item


@inject
def oscillator_to_pb(
    data, capabilities: ServerCapabilities = Provide[CapabilitiesContainer.capabilities]
) -> qua_config.QuaConfigOscillator:
    oscillator = qua_config.QuaConfigOscillator()
    if "intermediate_frequency" in data:
        oscillator.intermediate_frequency = int(data["intermediate_frequency"])
        if capabilities.supports_double_frequency:
            oscillator.intermediate_frequency_double = float(data["intermediate_frequency"])

    if "mixer" in data:
        oscillator.mixer = qua_config.QuaConfigMixerRef(mixer=data["mixer"])
        oscillator.mixer.lo_frequency = int(data.get("lo_frequency", 0))
        if capabilities.supports_double_frequency:
            oscillator.mixer.lo_frequency_double = float(data.get("lo_frequency", 0.0))

    return oscillator


@inject
def create_correction_entry(
    mixer_data,
    capabilities: ServerCapabilities = Provide[CapabilitiesContainer.capabilities],
) -> qua_config.QuaConfigCorrectionEntry:
    correction = qua_config.QuaConfigCorrectionEntry(
        frequency_negative=mixer_data["intermediate_frequency"] < 0,
        correction=qua_config.QuaConfigMatrix(
            v00=mixer_data["correction"][0],
            v01=mixer_data["correction"][1],
            v10=mixer_data["correction"][2],
            v11=mixer_data["correction"][3],
        ),
    )
    correction.frequency = abs(int(mixer_data["intermediate_frequency"]))
    correction.lo_frequency = int(mixer_data["lo_frequency"])
    if capabilities.supports_double_frequency:
        correction.frequency_double = abs(float(mixer_data["intermediate_frequency"]))
        correction.lo_frequency_double = float(mixer_data["lo_frequency"])

    return correction


def mixer_to_pb(data) -> qua_config.QuaConfigMixerDec:
    return qua_config.QuaConfigMixerDec(correction=[create_correction_entry(mixer) for mixer in data])


def element_thread_to_pb(name: str) -> qua_config.QuaConfigElementThread:
    return qua_config.QuaConfigElementThread(thread_name=name)


def dac_port_ref_to_pb(controller: str, number: int) -> qua_config.QuaConfigDacPortReference:
    return qua_config.QuaConfigDacPortReference(controller=controller, number=number)


def single_input_to_pb(controller: str, number: int) -> qua_config.QuaConfigSingleInput:
    return qua_config.QuaConfigSingleInput(port=dac_port_ref_to_pb(controller, number))


def adc_port_ref_to_pb(controller: str, number: int) -> qua_config.QuaConfigAdcPortReference:
    return qua_config.QuaConfigAdcPortReference(controller=controller, number=number)


def port_ref_to_pb(controller: str, number: int) -> qua_config.QuaConfigPortReference:
    return qua_config.QuaConfigPortReference(controller=controller, number=number)


def digital_input_port_ref_to_pb(data) -> qua_config.QuaConfigDigitalInputPortReference:
    digital_input = qua_config.QuaConfigDigitalInputPortReference(
        delay=int(data["delay"]),
        buffer=int(data["buffer"]),
    )
    if "port" in data:
        digital_input.port = port_ref_to_pb(data["port"][0], data["port"][1])

    return digital_input


def digital_output_port_ref_to_pb(
    data,
) -> qua_config.QuaConfigDigitalOutputPortReference:
    return qua_config.QuaConfigDigitalOutputPortReference(port=port_ref_to_pb(data[0], data[1]))


def octave_params_to_pb(octave_params: dict) -> qua_config.QuaConfigUpConverted:
    pb_instance = qua_config.QuaConfigUpConverted(
        rf_output_port=octave_models.OctaveOutputPort(
            octave_params["rf_output_port"][0],
            octave_models.OctaveRfOutputPortName[octave_params["rf_output_port"][1]],
        ),
        lo_source=octave_models.OctaveLoSourceInput[octave_params["lo_source"]],
        output_switch_state=qua_config.QuaConfigOutputSwitchState[octave_params.get("output_switch_state", "unset")],
        output_gain=octave_params.get("output_gain", 0),
        downconversion_lo_frequency=octave_params.get("downconversion_lo_frequency", 0.0),
    )
    if "downconversion_lo_source" in octave_params:
        pb_instance.downconversion_lo_source = octave_models.OctaveLoSourceInput[
            octave_params["downconversion_lo_source"]
        ]
    if "rf_input_port" in octave_params:
        pb_instance.rf_input_port = octave_models.OctaveRfInputPort(
            octave_params["rf_input_port"][0],
            octave_models.OctaveRfInputPortName[octave_params["rf_input_port"][1]],
        )
    return pb_instance


@inject
def element_to_pb(
    element_name,
    data,
    capabilities: ServerCapabilities = Provide[CapabilitiesContainer.capabilities],
) -> qua_config.QuaConfigElementDec():
    validate_oscillator(data)
    validate_output_smearing(data)
    validate_output_tof(data)
    validate_timetagging_parameters(data)
    validate_used_inputs(data)

    element = qua_config.QuaConfigElementDec()

    if "time_of_flight" in data:
        element.time_of_flight = int(data["time_of_flight"])

    if "smearing" in data:
        element.smearing = int(data["smearing"])

    if "intermediate_frequency" in data:
        element.intermediate_frequency = abs(int(data["intermediate_frequency"]))
        element.intermediate_frequency_oscillator = int(data["intermediate_frequency"])
        if capabilities.supports_double_frequency:
            element.intermediate_frequency_double = abs(float(data["intermediate_frequency"]))
            element.intermediate_frequency_oscillator_double = float(data["intermediate_frequency"])

        element.intermediate_frequency_negative = data["intermediate_frequency"] < 0

    if "thread" in data:
        element.thread = element_thread_to_pb(data["thread"])

    if "outputs" in data:
        for k, v in data["outputs"].items():
            element.outputs[k] = adc_port_ref_to_pb(v[0], v[1])

    if "digitalInputs" in data:
        for k, v in data["digitalInputs"].items():
            element.digital_inputs[k] = digital_input_port_ref_to_pb(v)

    if "digitalOutputs" in data:
        for k, v in data["digitalOutputs"].items():
            element.digital_outputs[k] = digital_output_port_ref_to_pb(v)

    if "operations" in data:
        for k, v in data["operations"].items():
            element.operations[k] = v

    if "singleInput" in data:
        (cont, port_id) = data["singleInput"]["port"]
        element.single_input = single_input_to_pb(cont, port_id)

    if "mixInputs" in data:
        mix_inputs = data["mixInputs"]
        (cont_I, port_id_I) = mix_inputs["I"]
        (cont_Q, port_id_Q) = mix_inputs["Q"]
        element.mix_inputs = qua_config.QuaConfigMixInputs(
            i=dac_port_ref_to_pb(cont_I, port_id_I),
            q=dac_port_ref_to_pb(cont_Q, port_id_Q),
            mixer=mix_inputs.get("mixer", ""),
        )

        lo_frequency = mix_inputs.get("lo_frequency", 0)
        element.mix_inputs.lo_frequency = int(lo_frequency)
        if capabilities.supports_double_frequency:
            element.mix_inputs.lo_frequency_double = float(lo_frequency)

        if "octave_params" in mix_inputs:
            element.mix_inputs.octave_params = octave_params_to_pb(mix_inputs["octave_params"])

    if "singleInputCollection" in data:
        element.single_input_collection = qua_config.QuaConfigSingleInputCollection(
            inputs={k: dac_port_ref_to_pb(v[0], v[1]) for k, v in data["singleInputCollection"]["inputs"].items()}
        )

    if "multipleInputs" in data:
        element.multiple_inputs = qua_config.QuaConfigMultipleInputs(
            inputs={k: dac_port_ref_to_pb(v[0], v[1]) for k, v in data["multipleInputs"]["inputs"].items()}
        )

    if "oscillator" in data:
        element.named_oscillator = data["oscillator"]
    elif "intermediate_frequency" not in data:
        element.no_oscillator = Empty()

    if "sticky" in data:
        if capabilities.supports_sticky_elements:
            element.sticky = qua_config.QuaConfigSticky(
                analog=data["sticky"].get("analog", True),
                digital=data["sticky"].get("digital", False),
                duration=data["sticky"].get("duration", 1),
            )
        else:
            if "digital" in data["sticky"] and data["sticky"]["digital"]:
                raise ConfigValidationException(
                    f"Server does not support digital sticky used in element " f"'{element_name}'"
                )
            element.hold_offset = qua_config.QuaConfigHoldOffset(duration=data["sticky"].get("duration", 1))

    elif "hold_offset" in data:
        if capabilities.supports_sticky_elements:
            element.sticky = qua_config.QuaConfigSticky(
                analog=True,
                digital=False,
                duration=data["hold_offset"].get("duration", 1),
            )
        else:
            element.hold_offset = qua_config.QuaConfigHoldOffset(duration=data["hold_offset"]["duration"])

    if "outputPulseParameters" in data:
        pulse_parameters = data["outputPulseParameters"]
        output_pulse_parameters = qua_config.QuaConfigOutputPulseParameters(
            signal_threshold=pulse_parameters["signalThreshold"],
        )

        signal_polarity = pulse_parameters["signalPolarity"].upper()
        if signal_polarity == "ABOVE" or signal_polarity == "ASCENDING":
            output_pulse_parameters.signal_polarity = qua_config.QuaConfigOutputPulseParametersPolarity.ASCENDING
        elif signal_polarity == "BELOW" or signal_polarity == "DESCENDING":
            output_pulse_parameters.signal_polarity = qua_config.QuaConfigOutputPulseParametersPolarity.DESCENDING

        if "derivativeThreshold" in pulse_parameters:
            output_pulse_parameters.derivative_threshold = pulse_parameters["derivativeThreshold"]
            polarity = pulse_parameters["derivativePolarity"].upper()
            if polarity == "ABOVE" or polarity == "ASCENDING":
                output_pulse_parameters.derivative_polarity = (
                    qua_config.QuaConfigOutputPulseParametersPolarity.ASCENDING
                )
            elif polarity == "BELOW" or polarity == "DESCENDING":
                output_pulse_parameters.derivative_polarity = (
                    qua_config.QuaConfigOutputPulseParametersPolarity.DESCENDING
                )

        element.output_pulse_parameters = output_pulse_parameters
    return element


def waveform_to_pb(data) -> qua_config.QuaConfigWaveformDec:
    wf = qua_config.QuaConfigWaveformDec()
    if data["type"] == "constant":
        wf.constant = qua_config.QuaConfigConstantWaveformDec(sample=data["sample"])
    elif data["type"] == "arbitrary":
        is_overridable = data.get("is_overridable", False)
        has_max_allowed_error = "max_allowed_error" in data
        has_sampling_rate = "sampling_rate" in data
        validate_arbitrary_waveform(is_overridable, has_max_allowed_error, has_sampling_rate)

        wf.arbitrary = qua_config.QuaConfigArbitraryWaveformDec(samples=data["samples"], is_overridable=is_overridable)

        if has_max_allowed_error:
            wf.arbitrary.max_allowed_error = data["max_allowed_error"]
        elif has_sampling_rate:
            wf.arbitrary.sampling_rate = data["sampling_rate"]
        elif not is_overridable:
            wf.arbitrary.max_allowed_error = 1e-4
    return wf


def digital_waveform_to_pb(data) -> qua_config.QuaConfigDigitalWaveformDec:
    return qua_config.QuaConfigDigitalWaveformDec(
        samples=[qua_config.QuaConfigDigitalWaveformSample(value=bool(s[0]), length=s[1]) for s in data["samples"]]
    )


def pulse_to_pb(data) -> qua_config.QuaConfigPulseDec:
    pulse = qua_config.QuaConfigPulseDec()

    if "length" in data:
        pulse.length = int(data["length"])

    if "operation" in data:
        if data["operation"] == "control":
            pulse.operation = qua_config.QuaConfigPulseDecOperation.CONTROL
        else:
            pulse.operation = qua_config.QuaConfigPulseDecOperation.MEASUREMENT

    if "digital_marker" in data:
        pulse.digital_marker = data["digital_marker"]

    if "integration_weights" in data:
        for k, v in data["integration_weights"].items():
            pulse.integration_weights[k] = v

    if "waveforms" in data:
        if "single" in data["waveforms"]:
            pulse.waveforms["single"] = data["waveforms"]["single"]

        elif "I" in data["waveforms"]:
            pulse.waveforms["I"] = data["waveforms"]["I"]
            pulse.waveforms["Q"] = data["waveforms"]["Q"]
    return pulse


def build_iw_sample(data) -> List[qua_config.QuaConfigIntegrationWeightSample]:
    if len(data) > 0 and not isinstance(data[0], tuple):
        data = np.round(2**-15 * np.round(np.array(data) / 2**-15), 20)
        new_data = []
        for s in data:
            if len(new_data) == 0 or new_data[-1][0] != s:
                new_data.append((s, 4))
            else:
                new_data[-1] = (new_data[-1][0], new_data[-1][1] + 4)
        data = new_data
    return [qua_config.QuaConfigIntegrationWeightSample(value=s[0], length=int(s[1])) for s in data]


def integration_weights_to_pb(data) -> qua_config.QuaConfigIntegrationWeightDec:
    iw = qua_config.QuaConfigIntegrationWeightDec(
        cosine=build_iw_sample(data["cosine"]), sine=build_iw_sample(data["sine"])
    )
    return iw


def load_config_pb(config) -> qua_config.QuaConfig:

    pb_config = qua_config.QuaConfig(v1_beta=qua_config.QuaConfigQuaConfigV1())

    def set_controllers():
        for k, v in config["controllers"].items():
            pb_config.v1_beta.controllers[k] = controller_to_pb(v)

    def set_octaves():
        for k, v in config.get("octaves", {}).items():
            pb_config.v1_beta.octaves[k] = octave_to_pb(v)

    def set_elements():
        for k, v in config["elements"].items():
            pb_config.v1_beta.elements[k] = element_to_pb(k, v)

    def set_pulses():
        for k, v in config["pulses"].items():
            pb_config.v1_beta.pulses[k] = pulse_to_pb(v)

    def set_waveforms():
        for k, v in config["waveforms"].items():
            pb_config.v1_beta.waveforms[k] = waveform_to_pb(v)

    def set_digital_waveforms():
        for k, v in config["digital_waveforms"].items():
            pb_config.v1_beta.digital_waveforms[k] = digital_waveform_to_pb(v)

    def set_integration_weights():
        for k, v in config["integration_weights"].items():
            pb_config.v1_beta.integration_weights[k] = integration_weights_to_pb(v)

    def set_mixers():
        for k, v in config["mixers"].items():
            pb_config.v1_beta.mixers[k] = mixer_to_pb(v)

    def set_oscillators():
        for k, v in config["oscillators"].items():
            pb_config.v1_beta.oscillators[k] = oscillator_to_pb(v)

    key_to_action = {
        "version": lambda: None,
        "controllers": set_controllers,
        "elements": set_elements,
        "pulses": set_pulses,
        "waveforms": set_waveforms,
        "digital_waveforms": set_digital_waveforms,
        "integration_weights": set_integration_weights,
        "mixers": set_mixers,
        "oscillators": set_oscillators,
        "octaves": set_octaves,
    }

    for key in config:
        key_to_action[key]()

    return pb_config
