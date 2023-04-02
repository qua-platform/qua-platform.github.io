from marshmallow import ValidationError

from qm.exceptions import ConfigValidationException


def validate_timetagging_parameters(data):
    if "outputPulseParameters" in data:
        pulseParameters = data["outputPulseParameters"]
        neededParameters = [
            "signalThreshold",
            "signalPolarity",
            "derivativeThreshold",
            "derivativePolarity",
        ]
        missingParameters = []
        for parameter in neededParameters:
            if parameter not in pulseParameters:
                missingParameters.append(parameter)
        if len(missingParameters) > 0:
            raise ConfigValidationException(
                "An element defining the output pulse parameters must either "
                f"define all of the parameters: {neededParameters}. "
                f"Parameters defined: {pulseParameters}"
            )
        validPolarity = {"ASCENDING", "DESCENDING", "ABOVE", "BELOW"}
        if data["outputPulseParameters"]["signalPolarity"].upper() not in validPolarity:
            raise ConfigValidationException(
                f"'signalPolarity' is {data['outputPulseParameters']['signalPolarity'].upper()} but it must be one of {validPolarity}"
            )
        if data["outputPulseParameters"]["derivativePolarity"].upper() not in validPolarity:
            raise ConfigValidationException(
                f"'derivativePolarity' is {data['outputPulseParameters']['derivativePolarity'].upper()} but it must be one of {validPolarity}"
            )


def validate_output_tof(data):
    if "outputs" in data and data["outputs"] != {} and "time_of_flight" not in data:
        raise ValidationError("An element with an output must have time_of_flight defined")
    if "outputs" not in data and "time_of_flight" in data:
        raise ValidationError("time_of_flight should be used only with elements that have outputs")


def validate_output_smearing(data):
    if "outputs" in data and data["outputs"] != {} and "smearing" not in data:
        raise ValidationError("An element with an output must have smearing defined")
    if "outputs" not in data and "smearing" in data:
        raise ValidationError("smearing should be used only with elements that have outputs")


def validate_oscillator(data):
    if "intermediate_frequency" in data and "oscillator" in data:
        raise ValidationError("'intermediate_frequency' and 'oscillator' cannot be defined together")


def validate_used_inputs(data):
    used_inputs = list(
        filter(
            lambda it: it in data,
            ["singleInput", "mixInputs", "singleInputCollection", "multipleInputs"],
        )
    )
    if len(used_inputs) > 1:
        raise ValidationError(
            f"Can't support more than a single input type. " f"Used {', '.join(used_inputs)}",
            field_name="",
        )


def validate_arbitrary_waveform(is_overridable, has_max_allowed_error, has_sampling_rate):
    if is_overridable and has_max_allowed_error:
        raise ValidationError("Overridable waveforms cannot have property 'max_allowed_error'")
    if is_overridable and has_sampling_rate:
        raise ValidationError("Overridable waveforms cannot have property 'sampling_rate_key'")
    if has_max_allowed_error and has_sampling_rate:
        raise ValidationError("Cannot use both 'max_allowed_error' and 'sampling_rate'")
