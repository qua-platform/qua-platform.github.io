import numpy as np

controller = "con1"

opx_analog_outputs_to_scope = (3, 6, 7, 9)
opx_digital_outputs_to_scope = (9,)

single_pulse_len = 200
long_pulse_len = 10000

wf_amp = 0.3
offsets = [0.0] * 10

lo1 = 5.525324e9
if1 = 50e6
lo2 = 5.18345e9
if2 = 0.0  # 50e6
lo_rr = 6.1423e9
if_rr = 50e6
if_paramp = 100e6
lo_parmap = 3.5323e9

w = 4.0
pad = 2
w1cos = w * np.ones(int(single_pulse_len // 4 + pad))
w1sin = 0.0 * np.zeros(int(single_pulse_len // 4 + pad))
w2cos = 0.0 * np.zeros(int(single_pulse_len // 4 + pad))
w2sin = w * np.ones(int(single_pulse_len // 4 + pad))
w1_prerot = np.vstack((w1cos, w1sin))
w2_prerot = np.vstack((w2cos, w2sin))

# rotate the integration weights in the IQ plane
rot_phase_5 = -0.0
rot_mat_5 = np.array(
    [
        [np.cos(rot_phase_5), -np.sin(rot_phase_5)],
        [np.sin(rot_phase_5), np.cos(rot_phase_5)],
    ]
)
rot_phase_6 = -0.3 + np.pi / 2 - 0.1
rot_mat_6 = np.array(
    [
        [np.cos(rot_phase_6), -np.sin(rot_phase_6)],
        [np.sin(rot_phase_6), np.cos(rot_phase_6)],
    ]
)

w1_5 = rot_mat_5 @ w1_prerot
w2_5 = rot_mat_5 @ w2_prerot

w1_6 = rot_mat_6 @ w1_prerot
w2_6 = rot_mat_6 @ w2_prerot

config = {
    "version": 1,
    "controllers": {
        controller: {
            "type": "opx1",
            "analog_outputs": {i + 1: {"offset": offsets[i]} for i in range(10)},
            "analog_inputs": {i + 1: {"offset": offsets[i]} for i in range(2)},
        }
    },
    "elements": {
        "qb1": {
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
                "lo_frequency": lo1,
                "mixer": "mxr_qb1",
            },
            "intermediate_frequency": if1,
            "operations": {
                "pulse1": "pulse1_in",
                "pi_pulse": "pi_pulse_qb1_in",
            },
        },
        "rr1": {
            "mixInputs": {
                "I": ("con1", 3),
                "Q": ("con1", 4),
                "lo_frequency": lo_rr,
                #'mixer': 'mxr_rr'
            },
            "intermediate_frequency": if_rr,
            "operations": {"pulse1": "pulse1_in", "ro_pulse": "meas_pulse_in"},
            "time_of_flight": 28,
            "smearing": 10,
            "outputs": {"out1": ("con1", 1), "out2": ("con1", 2)},
        },
        "paramp": {
            "mixInputs": {
                "I": ("con1", 7),
                "Q": ("con1", 8),
                "lo_frequency": lo_parmap,
                "mixer": "mxr_paramp",
            },
            "intermediate_frequency": if_paramp,
            "operations": {
                "pulse1": "pulse1_in",
            },
        },
    },
    "pulses": {
        "pulse1_in": {
            "operation": "control",
            "length": single_pulse_len,
            "waveforms": {
                "I": "wf1",
                "Q": "wf_zero",
            },
        },
        "pi_pulse_qb1_in": {
            "operation": "control",
            "length": single_pulse_len,
            "waveforms": {
                "I": "wf1",
                "Q": "wf_zero",
            },
        },
        "pi_pulse_qb2_in": {
            "operation": "control",
            "length": single_pulse_len,
            "waveforms": {
                "I": "wf1",
                "Q": "wf_zero",
            },
        },
        "meas_pulse_in": {
            "operation": "measurement",
            "length": single_pulse_len,
            "waveforms": {
                "I": "wf_meas",
                "Q": "wf_zero",
            },
            "integration_weights": {
                "integ_w_cos": "integW1",
                "integ_w_sin": "integW2",
            },
            "digital_marker": "trig_wf0",
        },
    },
    "digital_waveforms": {"trig_wf0": {"samples": [(1, single_pulse_len), (0, 0)]}},
    "waveforms": {
        "wf1": {"type": "constant", "sample": 0.1},
        "wf_meas": {"type": "constant", "sample": wf_amp},
        "wf_zero": {"type": "constant", "sample": 0.0},
    },
    "integration_weights": {
        "integW1": {
            "cosine": w1cos.tolist(),
            "sine": w1sin.tolist(),
        },
        "integW2": {
            "cosine": w2_5[0, :].tolist(),
            "sine": w2_5[1, :].tolist(),
        },
        "integW1_6": {
            "cosine": w1_6[0, :].tolist(),
            "sine": w1_6[1, :].tolist(),
        },
        "integW2_6": {
            "cosine": w2_6[0, :].tolist(),
            "sine": w2_6[1, :].tolist(),
        },
    },
    "mixers": {
        "mxr_rr": [
            {
                "intermediate_frequency": if_rr,
                "lo_frequency": lo_rr,
                "correction": [1.0, 0.0, 0.0, 1.0],
            },
        ],
        "mxr_qb1": [
            {
                "intermediate_frequency": if1,
                "lo_frequency": lo1,
                "correction": [1.0, 0.0, 0.0, 1.0],
            }
        ],
        "mxr_qb2": [
            {
                "intermediate_frequency": if2,
                "lo_frequency": lo2,
                "correction": [1.0, 0.0, 0.0, 1.0],
            }
        ],
        "mxr_paramp": [
            {
                "intermediate_frequency": if_paramp,
                "lo_frequency": lo_parmap,
                "correction": [1.0, 0.0, 0.0, 1.0],
            }
        ],
    },
}
