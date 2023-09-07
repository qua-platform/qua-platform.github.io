import numpy as np

pulse_duration = 5700
eom_warmpup = 1000

config = {
    "version": 1,
    "controllers": {
        "con1": {
            "analog_outputs": {
                f"{i}": {
                    "offset": 0,
                    "filter": {
                        "feedforward": [0.0] * (i - 1) + [1.0] + [0.0] * (10 - i),
                        "feedback": [],
                    },
                    "delay": 36.0,
                    "shareable": np.random.choice([True, False], 1)[0],
                    "crosstalk": {f"{k}": np.random.random() for k in range(1, 11)}
                }
                for i in range(1, 11)
            },
            "digital_outputs": {f"{i}": {"shareable": np.random.choice([True, False], 1)[0]} for i in range(1, 11)},
            "analog_inputs": {
                f"{i}": {
                    "gain_db": 10,
                    "offset": 0.1,
                    "shareable": np.random.choice([True, False], 1)[0]
                }
                for i in range(1, 11)
            },
            "digital_inputs": {
                f"{i}": {
                    "polarity": np.random.choice(["RISING", "FALLING"], 1)[0],
                    "deadtime": 40.0,
                    "threshold": 0.1,
                    "shareable": np.random.choice([True, False], 1)[0]
                }
                for i in range(1, 5)

            }
        },
        "con2": {
            "analog_outputs": {f"{i}": {"offset": 0.0} for i in range(1, 11)},
            "digital_outputs": {f"{i}": {} for i in range(1, 11)},
        },
        "con3": {
            "analog_outputs": {f"{i}": {"offset": 0.0} for i in range(1, 11)},
            "digital_outputs": {f"{i}": {} for i in range(1, 11)},
        },
        "con4": {
            "analog_outputs": {f"{i}": {"offset": 0.0} for i in range(1, 11)},
            "digital_outputs": {f"{i}": {} for i in range(1, 11)},
        },
        "con5": {
            "analog_outputs": {f"{i}": {"offset": 0.0} for i in range(1, 11)},
            "digital_outputs": {f"{i}": {} for i in range(1, 11)},
        },
    },

    "elements": {
        "oneq_dump_ha": {
            "intermediate_frequency": 71000000.0,
            "operations": {
                "empty": "empty_pulse",
                "dump_idle": "dump_idle",
                "SquarePulse_d": "SquarePulse_d",
                "SquarePulse_e": "SquarePulse_e",
                "SquarePulse_f": "SquarePulse_f",
                "SquarePulse_g": "SquarePulse_g",
            },
            "singleInput": {"port": ("con2", 7)},
        },
        "oneq_dump_va": {
            "intermediate_frequency": 139000000.0,
            "operations": {
                "empty": "empty_pulse",
                "dump_idle": "dump_idle",
                "SquarePulse_d": "SquarePulse_d",
                "SquarePulse_h": "SquarePulse_h",
                "SquarePulse_f": "SquarePulse_f",
                "SquarePulse_g": "SquarePulse_g",
            },
            "singleInput": {"port": ("con2", 9)},
        },
        "oneq_dump_hb": {
            "intermediate_frequency": 139000000.0,
            "operations": {
                "empty": "empty_pulse",
                "dump_idle": "dump_idle",
                "SquarePulse_d": "SquarePulse_d",
                "SquarePulse_e": "SquarePulse_e",
                "SquarePulse_f": "SquarePulse_f",
                "SquarePulse_g": "SquarePulse_g",
            },
            "singleInput": {"port": ("con3", 6)},
        },
        "oneq_dump_vb": {
            "intermediate_frequency": 71000000.0,
            "operations": {
                "empty": "empty_pulse",
                "dump_idle": "dump_idle",
                "SquarePulse_d": "SquarePulse_d",
                "SquarePulse_h": "SquarePulse_h",
                "SquarePulse_f": "SquarePulse_f",
                "SquarePulse_g": "SquarePulse_g",
            },
            "singleInput": {"port": ("con3", 8)},
        },
        "oneq_0_ha": {
            "intermediate_frequency": 102268000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con2", 7)},
        },
        "oneq_1_ha": {
            "intermediate_frequency": 103542000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con2", 7)},
        },
        "oneq_2_ha": {
            "intermediate_frequency": 104816000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con2", 7)},
        },
        "oneq_3_ha": {
            "intermediate_frequency": 106090000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con2", 7)},
        },
        "oneq_4_ha": {
            "intermediate_frequency": 107365000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con2", 7)},
        },
        "oneq_5_ha": {
            "intermediate_frequency": 108639000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con2", 7)},
        },
        "oneq_6_ha": {
            "intermediate_frequency": 109913000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con2", 7)},
        },
        "oneq_0_va": {
            "intermediate_frequency": 101442000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con2", 9)},
        },
        "oneq_1_va": {
            "intermediate_frequency": 102689000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con2", 9)},
        },
        "oneq_2_va": {
            "intermediate_frequency": 103937000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con2", 9)},
        },
        "oneq_3_va": {
            "intermediate_frequency": 105184000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con2", 9)},
        },
        "oneq_4_va": {
            "intermediate_frequency": 106431000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con2", 9)},
        },
        "oneq_5_va": {
            "intermediate_frequency": 107679000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con2", 9)},
        },
        "oneq_6_va": {
            "intermediate_frequency": 108926000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con2", 9)},
        },
        "oneq_6_va_without_if": {
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con2", 9)},
        },
        "oneq_eoma": {
            "intermediate_frequency": 317853572.0,
            "operations": {"empty": "empty_pulse_IQ", "SquarePulse_c": "SquarePulse_c"},
            "mixInputs": {
                "I": ("con1", 4),
                "Q": ("con1", 3),
                "mixer": "mxr_a",
                "lo_frequency": 9400000000.0,
            },
        },
        "oneq_0_hb": {
            "intermediate_frequency": 108114000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con3", 6)},
        },
        "oneq_1_hb": {
            "intermediate_frequency": 106839000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con3", 6)},
        },
        "oneq_2_hb": {
            "intermediate_frequency": 105565000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con3", 6)},
        },
        "oneq_3_hb": {
            "intermediate_frequency": 104291000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con3", 6)},
        },
        "oneq_4_hb": {
            "intermediate_frequency": 103017000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con3", 6)},
        },
        "oneq_5_hb": {
            "intermediate_frequency": 101743000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con3", 6)},
        },
        "oneq_6_hb": {
            "intermediate_frequency": 100469000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_a": "SquarePulse_a"},
            "singleInput": {"port": ("con3", 6)},
        },
        "oneq_0_vb": {
            "intermediate_frequency": 107881000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con3", 8)},
        },
        "oneq_1_vb": {
            "intermediate_frequency": 106633000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con3", 8)},
        },
        "oneq_2_vb": {
            "intermediate_frequency": 105386000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con3", 8)},
        },
        "oneq_3_vb": {
            "intermediate_frequency": 104139000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con3", 8)},
        },
        "oneq_4_vb": {
            "intermediate_frequency": 102891000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con3", 8)},
        },
        "oneq_5_vb": {
            "intermediate_frequency": 101644000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con3", 8)},
        },
        "oneq_6_vb": {
            "intermediate_frequency": 100397000.0,
            "operations": {"empty": "empty_pulse", "SquarePulse_b": "SquarePulse_b"},
            "singleInput": {"port": ("con3", 8)},
        },
        "oneq_eomb": {
            "intermediate_frequency": -297852122.0,
            "operations": {"empty": "empty_pulse_IQ", "SquarePulse_c": "SquarePulse_c"},
            "mixInputs": {
                "I": ("con1", 4),
                "Q": ("con1", 3),
                "mixer": "mxr_b",
                "lo_frequency": 9400000000.0,
            },
        },
        "OPXs": {
            "operations": {"trig": "trig_pulse"},
            "digitalInputs": {
                "OPX2": {
                    "port": ("con1", 1),
                    "delay": 0,
                    "buffer": 0,
                },
                "OPX3": {
                    "port": ("con1", 2),
                    "delay": 0,
                    "buffer": 0,
                },
                "OPX4": {
                    "port": ("con1", 3),
                    "delay": 0,
                    "buffer": 0,
                },
                "OPX5": {
                    "port": ("con1", 4),
                    "delay": 0,
                    "buffer": 0,
                },
                "scope": {
                    "port": ("con1", 5),
                    "delay": 0.0,
                    "buffer": 0.0,
                },
            },
        },
        "RR" : {
            "intermediate_frequency": -297852122.0,
            "operations": {"readout": "readout_pulse"},
            "mixInputs": {
                "I": ("con1", 4),
                "Q": ("con1", 3),
                "mixer": "mxr_b",
                "lo_frequency": 9400000000.0,
            },
            "outputs": {
                "out1": ("con1", 1),
                "out2": ("con1", 2),
            },
            "time_of_flight": 80.0,
            "smearing": 0.0,

        },
        'digitalout_element': {
            'mixInputs': {
                'I': ('con1', 1),
                'Q': ('con1', 2),
                'lo_frequency': 2e9,
                'mixer': 'mixer_qubit'
            },
            'digitalOutputs': {
                'out1': ('con1', 2)
            },
            'operations': {
                'CW': 'CW',
                'saturation': 'saturation_pulse',
                'gaussian': 'gaussian_pulse',
                'pi': 'pi_pulse',
            }
        },
        'oscillator_element': {
            'mixInputs': {
                'I': ('con1', 1),
                'Q': ('con1', 2),
                'lo_frequency': 2e9,
                'mixer': 'mixer_qubit'
            },
            'oscillator': "osc",  # Can be any string
            'operations': {
                'CW': 'CW',
                'saturation': 'saturation_pulse',
                'gaussian': 'gaussian_pulse',
                'pi': 'pi_pulse',
            }
        },
        'hold_offset_element': {  # element to apply the DC offset on I
            'singleInput': {
                'port': ('con1', 1)
            },
            'hold_offset': {'duration': 1},  # Can be any integer > 1
            'operations': {
                'DC_offset': 'DC_offset_pulse'
            }
        },
        'sticky_element': {  # element to apply the DC offset on I
            'singleInput': {
                'port': ('con1', 1)
            },
            'sticky': {'analog': True, 'duration': 16, 'digital': True},  # Can be any integer % 4 == 0
            'operations': {
                'DC_offset': 'DC_offset_pulse'
            }
        },
        'sticky_element2': {  # element to apply the DC offset on I
            'singleInput': {
                'port': ('con1', 1)
            },
            'sticky': {'analog': True, 'digital': True},
            'operations': {
                'DC_offset': 'DC_offset_pulse'
            }
        },
        "tagging_element": {
            "singleInput": {"port": ("con1", 1)},  # not used
            "digitalInputs": {
                "marker": {
                    "port": ("con1", 1),
                    "delay": 10,
                    "buffer": 0,
                },
            },
            "operations": {
                "readout": "readout_pulse",
            },
            "outputs": {"out1": ("con1", 1)},
            "outputPulseParameters": {
                "signalThreshold": -500,  # Can be from -2048 to +2047
                "signalPolarity": "Below",  # Can be "Above", "Below", "Ascending", "Descending"
                "derivativeThreshold": -2048,  # Can be from -2048 to +2047
                "derivativePolarity": "Above",  # Can be "Above", "Below", "Ascending", "Descending"
            },
            "time_of_flight": 180,
            "smearing": 0,
        },
        'multipleInputs_element': {
            'multipleInputs': {  # An example element that will play from ports 1 and 2 simultaneously
                'inputs': {
                    'input1': ('con1', 1),  # Name (key) can be any string
                    'input2': ('con1', 2)
                }
            },
            'operations': {
                'const': 'const_pulse',
            },
        },
        'singleInputCollection_element': {
            "singleInputCollection": {  # Doesn't have to be all of them.
                "inputs": {
                    "o1": ('con1', 1),  # Name (key) can be any string
                    "o2": ('con1', 2),
                    "o3": ('con1', 3),
                    "o4": ('con1', 4),
                    "o5": ('con1', 5),
                    "o6": ('con1', 6),
                    "o7": ('con1', 7),
                    "o8": ('con1', 8),
                    "o9": ('con1', 9),
                    "o10": ('con1', 10),
                }
            },
            'digitalInputs': {
                'laser': {
                    'buffer': 0,
                    'delay': 0,
                    'port': ('con1', 1)},
            },
            "outputs": {
                'out1': ("con1", 1)
            },
            'time_of_flight': 28,
            'smearing': 0,
            'intermediate_frequency': 100e6,
            'operations': {
                'pi': 'pi',
            },
        },
        "thread_element": {
            "thread": "d",  # Can be any string
            "digitalInputs": {
                "laser1_AOM": {
                    "port": ("con1", 1),
                    "delay": 0,
                    "buffer": 0,
                },
            },
            "operations": {
                "initialization": "initialization_pulse",
            },
        },

    },
    "pulses": {
        "trig_pulse": {
            "operation": "control",
            "length": 100,
            "digital_marker": "trig_wf0",
        },
        "empty_pulse": {
            "operation": "control",
            "length": 100,
            "waveforms": {"single": "zero_wf"},
        },
        "empty_pulse_IQ": {
            "operation": "control",
            "length": 100,
            "waveforms": {"I": "zero_wf", "Q": "zero_wf"},
        },
        "empty_pulse_dig": {
            "digital_marker": "trig_empty",
            "length": 100,
            "operation": "control",
        },
        "dump_idle": {
            "operation": "control",
            "length": 208,
            "waveforms": {"single": "dump_idle"},
        },
        "marker_pulse": {
            "digital_marker": "trig_wf0",
            "length": 100.0,
            "operation": "control",
        },
        "SquarePulse_a": {
            "operation": "control",
            "length": pulse_duration,
            "waveforms": {"single": "SquarePulse_a"},
        },
        "SquarePulse_b": {
            "operation": "control",
            "length": pulse_duration,
            "waveforms": {"single": "SquarePulse_b"},
        },
        "SquarePulse_c": {
            "operation": "control",
            "length": pulse_duration - 2 * eom_warmpup,
            "waveforms": {"I": "SquarePulse_c_I", "Q": "SquarePulse_c_Q"},
        },
        "SquarePulse_d": {
            "operation": "control",
            "length": pulse_duration,
            "waveforms": {"single": "SquarePulse_d"},
        },
        "SquarePulse_e": {
            "operation": "control",
            "length": pulse_duration,
            "waveforms": {"single": "SquarePulse_e"},
        },
        "SquarePulse_f": {
            "operation": "control",
            "length": 67000000,
            "waveforms": {"single": "SquarePulse_f"},
        },
        "SquarePulse_g": {
            "operation": "control",
            "length": 31250000,
            "waveforms": {"single": "SquarePulse_g"},
        },
        "SquarePulse_h": {
            "operation": "control",
            "length": pulse_duration,
            "waveforms": {"single": "SquarePulse_h"},
        },
        "readout_pulse": {
            "operation": "measurement",
            "length": 100,
            "waveforms": {
                "I": "readout_wf",
                "Q": "zero_wf",
            },
            "integration_weights": {
                "cos": "integW1",
                "sin": "integW2",
            },
            "digital_marker": "ON",
        },
    },
    "waveforms": {
        "zero_wf": {"type": "constant", "sample": 0.0},
        "dump_idle": {"type": "constant", "sample": 0.25},  # 0.12399999999999999},
        "SquarePulse_a": {"type": "constant", "sample": 0.25},  # 0.03201666232864798},
        "SquarePulse_b": {"type": "constant", "sample": 0.2},  # 0.11979538110183267},
        "SquarePulse_c_I": {"type": "constant", "sample": 0.2},  # 0.37},
        "SquarePulse_c_Q": {"type": "constant", "sample": 0.2},  # 0.0},
        "SquarePulse_d": {"type": "constant", "sample": 0.25},  # 0.12399999999999999},
        "SquarePulse_e": {"type": "constant", "sample": 0.2},  # 0.09055679617418746},
        "SquarePulse_f": {"type": "constant", "sample": 0.2},  # 0.12399999999999999},
        "SquarePulse_g": {"type": "constant", "sample": 0.2},  # 0.12399999999999999},
        "SquarePulse_h": {"type": "constant", "sample": 0.2},  # 0.03201666232864799}},
        "test": {"type": "arbitrary", "samples": [i / 300 for i in range(100)]},
        "test2": {
            "type": "arbitrary",
            "is_overridable": True,
            "samples": [i / 300 for i in range(100)],
        },
    },
    "digital_waveforms": {
        "trig_wf0": {
            "samples": ((1, 0),),
        },
        "trig_empty": {
            "samples": ((0, 0),),
        },
    },
    "integration_weights": {
        "long_integW1": {
            "cosine": [1.0] * int(pulse_duration / 4),
            "sine": [0.0] * int(pulse_duration / 4),
        },
        "long_integW2": {
            "cosine": [0.0] * int(pulse_duration / 4),
            "sine": [1.0] * int(pulse_duration / 4),
        },
        "integW1": {
            "cosine": [(1.0, 100.0)],
            "sine": [(0.0, 100)],
        },
        "integW2": {
            "cosine": [(1.0, 100)],
            "sine": [(0.0, 100)],
        },
        "optW1": {
            "cosine": [1.0] * int(pulse_duration / 4),
            "sine": [0.0] * int(pulse_duration / 4),
        },
        "optW2": {
            "cosine": [0.0] * int(pulse_duration / 4),
            "sine": [1.0] * int(pulse_duration / 4),
        },
    },
    "mixers": {
        "mxr_a": [
            {
                "intermediate_frequency": 317853572.0,
                "lo_frequency": 9400000000.0,
                "correction": (1.0, 0.08772399329615435, 0.0, 0.9447909414200926),
            },
        ],
        "mxr_b": [
            {
                "intermediate_frequency": -297852122.0,
                "lo_frequency": 9400000000.0,
                "correction": (1.0, -0.13837314017589, 0.0, 1.0407506906698691),
            },
        ],
    },
    "oscillators": {
        "osc": {
            "intermediate_frequency": -125000.0,
            "lo_frequency": 150000.0,
            "mixer": "mxr_a"
        },
        "osc1": {
            "lo_frequency": 150000.0,
            "mixer": "mxr_a"
        },
        "osc2": {
            "mixer": "mxr_a"
        }
    },
}
