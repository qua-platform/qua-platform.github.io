import numpy as np

offset_amp = 2**-3  # (0.125)


def _iq_imbalance_corr(g, phi):
    c = np.cos(phi)
    s = np.sin(phi)
    n = 1 / ((1 - g**2) * (2 * c**2 - 1))
    return [float(n * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]]


def _get_frequencies(if_freq, optimizer_parameters):
    down_mixer_offset = optimizer_parameters["calibration_offset_frequency"]
    signal_freq = if_freq - down_mixer_offset
    image_freq = -if_freq - down_mixer_offset
    return down_mixer_offset, signal_freq, image_freq


def _prep_config(iq_channels, adc_channels, if_freq, lo_freq, optimizer_parameters):
    i0_offset = 0
    q0_offset = 0
    g = 0.0
    phi = 0.0
    calibration_amp = 0.125
    calibration_pulse_length = 10e3
    time_of_flight = 192
    correction_matrix = _iq_imbalance_corr(g, phi)

    down_mixer_offset, signal_freq, image_freq = _get_frequencies(
        if_freq, optimizer_parameters
    )

    i_port = iq_channels[0]
    q_port = iq_channels[1]
    controller_names = set(
        [ch[0] for ch in iq_channels] + [ch[0] for ch in adc_channels]
    )
    controllers = {
        name: {
            "type": "opx1",
        }
        for name in controller_names
    }
    controllers[i_port[0]]["analog_outputs"] = {}
    controllers[i_port[0]]["analog_outputs"][i_port[1]] = {"offset": i0_offset}
    controllers[q_port[0]]["analog_outputs"][q_port[1]] = {"offset": q0_offset}
    for port in adc_channels:
        controllers[port[0]]["analog_inputs"] = {}
    for port in adc_channels:
        controllers[port[0]]["analog_inputs"][port[1]] = {"offset": 0.0}

    config = {
        "version": 1,
        "controllers": controllers,
        "elements": {
            "IQmixer": {  # IQ mixer element
                "mixInputs": {
                    "I": i_port,
                    "Q": q_port,
                    "lo_frequency": lo_freq,
                    "mixer": "Correction_mixer",
                },
                "intermediate_frequency": if_freq,
                "operations": {
                    "calibration": "calibration_pulse",
                    "calibration_long": "long_calibration_pulse",
                },
                "digitalInputs": {},  # This is being added afterwards
            },
            "I_offset": {  # element to apply the DC offset on I
                "singleInput": {"port": i_port},
                "hold_offset": {"duration": 1},
                "operations": {"DC_offset": "DC_offset_pulse"},
            },
            "Q_offset": {  # element to apply the DC offset on Q
                "singleInput": {"port": q_port},
                "hold_offset": {"duration": 1},
                "operations": {"DC_offset": "DC_offset_pulse"},
            },
            "signal_analyzer": {
                "intermediate_frequency": signal_freq,
                "mixInputs": {
                    "I": i_port,
                    "Q": q_port,
                    "lo_frequency": lo_freq,
                    "mixer": "Correction_mixer",
                },
                "operations": {
                    "Analyze": "Analyze_pulse",
                },
                "outputs": {"out1": adc_channels[0], "out2": adc_channels[1]},
                "time_of_flight": time_of_flight,
                "smearing": 0,
            },
            "lo_analyzer": {
                "intermediate_frequency": -down_mixer_offset,
                "mixInputs": {
                    "I": i_port,
                    "Q": q_port,
                    "lo_frequency": lo_freq,
                    "mixer": "Correction_mixer",
                },
                "operations": {
                    "Analyze": "Analyze_pulse",
                },
                "outputs": {"out1": adc_channels[0], "out2": adc_channels[1]},
                "time_of_flight": time_of_flight,
                "smearing": 0,
            },
            "image_analyzer": {
                "intermediate_frequency": image_freq,
                "mixInputs": {
                    "I": i_port,
                    "Q": q_port,
                    "lo_frequency": lo_freq,
                    "mixer": "Correction_mixer",
                },
                "operations": {
                    "Analyze": "Analyze_pulse",
                },
                "outputs": {"out1": adc_channels[0], "out2": adc_channels[1]},
                "time_of_flight": time_of_flight,
                "smearing": 0,
            },
        },
        "pulses": {
            "calibration_pulse": {
                "operation": "control",
                "length": calibration_pulse_length,
                "waveforms": {
                    "I": "readout_wf",
                    "Q": "zero_wf",
                },
                "digital_marker": "ON",
            },
            "long_calibration_pulse": {
                "operation": "control",
                "length": calibration_pulse_length * 100,
                "waveforms": {
                    "I": "readout_wf",
                    "Q": "zero_wf",
                },
                "digital_marker": "ON",
            },
            "DC_offset_pulse": {
                "operation": "control",
                "length": calibration_pulse_length,
                "waveforms": {"single": "DC_offset_wf"},
            },
            "Analyze_pulse": {
                "operation": "measurement",
                "length": calibration_pulse_length,
                "waveforms": {
                    "I": "zero_wf",
                    "Q": "zero_wf",
                },
                "integration_weights": {
                    "integW_cos": "integW_cosine",
                    "integW_sin": "integW_sine",
                    "integW_minus_sin": "integW_minus_sine",
                },
                "digital_marker": "ON",
            },
        },
        "waveforms": {
            "readout_wf": {
                "type": "constant",
                "sample": calibration_amp,
            },
            "zero_wf": {
                "type": "constant",
                "sample": 0.0,
            },
            "DC_offset_wf": {"type": "constant", "sample": offset_amp},
        },
        "digital_waveforms": {
            "ON": {"samples": [(1, 0)]},
            "OFF": {"samples": [(0, 0)]},
        },
        "integration_weights": {
            "integW_cosine": {
                "cosine": [1.0] * int(calibration_pulse_length / 4),
                "sine": [0.0] * int(calibration_pulse_length / 4),
            },
            "integW_sine": {
                "cosine": [0.0] * int(calibration_pulse_length / 4),
                "sine": [1.0] * int(calibration_pulse_length / 4),
            },
            "integW_minus_sine": {
                "cosine": [0.0] * int(calibration_pulse_length / 4),
                "sine": [-1.0] * int(calibration_pulse_length / 4),
            },
        },
        "mixers": {
            "Correction_mixer": [
                {
                    "intermediate_frequency": if_freq,
                    "lo_frequency": lo_freq,
                    "correction": correction_matrix,
                },
                {
                    "intermediate_frequency": signal_freq,
                    "lo_frequency": lo_freq,
                    "correction": correction_matrix,
                },
                {
                    "intermediate_frequency": -down_mixer_offset,
                    "lo_frequency": lo_freq,
                    "correction": correction_matrix,
                },
                {
                    "intermediate_frequency": image_freq,
                    "lo_frequency": lo_freq,
                    "correction": correction_matrix,
                },
            ],
        },
    }

    return config
