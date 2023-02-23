flo1 = 0.85  # qubit
flo2 = 1.15  # resonator

sys_config = {
    "qubits": {
        "qb1": {
            "freq_ghz": 0.8,
            "drive_coupling_ghz": 0.4,
            "t1_nsec": 1 / 0.0007,
            "anharmonicity_ghz": 0.0,
        }
    },
    "resonators": {
        "rr1": {
            "freq_ghz": 1.1,  # resonator frequency
            "k_int_ghz": 0.1,  # internal damping rate
            "k_ext_ghz": 0.1,  # external coupling/damping rate
            "sigma": 0.005,  # standard deviation of steady state distribution (in units of res amplitude)
        }
    },
    "qubit_res_coupling": {"rr1": ["qb1", {"coupling_strength": 0.1}]},
}

analog_config = {
    "upsampling_factor": 10,  # what is the sampling rate of the simulator time above that of OPX
    "inputs": [
        "qb1:I",
        "qb1:Q",
        "rr1:I",
        "rr1:Q",
    ],  # this must be the same names as in analogOutConnection
    "upconversion_components": {  # available components for now: dac, iq_mixer, fridge_line
        "dac1_i": {"type": "dac", "input_name": "qb1:I"},
        "dac1_q": {"type": "dac", "input_name": "qb1:Q"},
        "dac2_i": {"type": "dac", "input_name": "rr1:I"},
        "dac2_q": {"type": "dac", "input_name": "rr1:Q"},
        "mxr1": {
            "type": "iq_mixer",
            "input_names": {"i": "dac1_i", "q": "dac1_q"},
            "properties": {"f_lo": flo1},
        },
        "mxr2": {
            "type": "iq_mixer",
            "input_names": {"i": "dac2_i", "q": "dac2_q"},
            "properties": {"f_lo": flo2},
        },
        "fl1": {
            "type": "fridge_line",
            "input_name": "mxr1",
        },
        "fl2": {
            "type": "fridge_line",
            "input_name": "mxr2",
        },
    },
    "downconversion_components": {  # available components for now: adc, mixer
        "mxr1": {"type": "mixer", "input_name": "rr1", "properties": {"f_lo": flo2}},
        "adc1": {
            "type": "adc",
            "input_name": "mxr1",
        },
    },
    "element_ports": {  # this is the type and name of each element in the simulator. Must be consistent with sys_config
        "qb1": {"element_type": "qubit", "upconversion_component": "fl1"},
        "rr1": {"element_type": "resonator", "upconversion_component": "fl2"},
    },
    "outputs": {"rr1_out": "adc1"},  # output must be connected to ADC
}
