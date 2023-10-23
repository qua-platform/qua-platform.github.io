from qm.quantum_machines_manager import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
from qm import LoopbackInterface
import numpy as np


def gauss(amplitude, mu, sigma, length):
    t = np.linspace(-length / 2, length / 2 - 1, length)
    gauss_wave = amplitude * np.exp(-((t - mu) ** 2) / (2 * sigma**2))
    return [float(x) for x in gauss_wave]


# Readout parameters
signal_threshold = -500

# Delays
detection_delay = 40

pulse_len = 100
gauss_pulse = gauss(0.4, 0, 10, pulse_len)
meas_len = 1000

config = {
    "version": 1,
    "controllers": {
        "con1": {
            "type": "opx1",
            "analog_outputs": {
                1: {"offset": +0.0},
                2: {"offset": +0.0},
            },
            "digital_outputs": {
                1: {},
            },
            "analog_inputs": {
                1: {"offset": 0.0},
            },
        }
    },
    "elements": {
        "analog_1": {
            "mixInputs": {"I": ("con1", 1), "Q": ("con1", 2)},
            "digitalInputs": {
                "laser": {"buffer": 0, "delay": 0, "port": ("con1", 1)},
            },
            "intermediate_frequency": 10e6,
            "operations": {
                "gaussian": "gaussianPulse",
            },
        },
    },
    "pulses": {
        "gaussianPulse": {
            "operation": "control",
            "length": pulse_len,
            "waveforms": {"I": "gauss_wf", "Q": "gauss_wf"},
            "digital_marker": "ON",
        },
        "digital_ON": {
            "digital_marker": "ON",
            "length": 100,
            "operation": "control",
        },
        "readout_pulse": {
            "operation": "measurement",
            "length": meas_len,
            "digital_marker": "ON",
            "waveforms": {"single": "zero_wf"},
        },
    },
    "digital_waveforms": {
        "ON": {"samples": [(1, 0)]},
    },
    "waveforms": {
        "const_wf": {"type": "constant", "sample": 0.4},
        "zero_wf": {"type": "constant", "sample": 0.0},
        "gauss_wf": {"type": "arbitrary", "samples": gauss_pulse},
    },
}


def test_we_have_all_elements(host_port):
    with program() as prog:
        play("gaussian", "analog_1")

    qmm = QuantumMachinesManager(**host_port)

    job = qmm.simulate(
        config, prog, SimulationConfig(4500, simulation_interface=LoopbackInterface(([("con1", 1, "con1", 1)])))
    )
    waveform_report = job.get_simulated_waveform_report()
    ref_dict = {
        "analog_waveforms": [
            {
                "waveform_name": "gauss_wf",
                "pulse_name": "OriginPulseName=gaussian",
                "length": 100,
                "timestamp": 216,
                "iq_info": {"isPartOfIq": True, "iqGroupId": 0.0, "isI": True, "isQ": False},
                "element": "analog_1",
                "output_ports": [1],
                "controller": "con1",
                "pulser": {"controllerName": "con1", "pulserIndex": 0.0},
                "current_amp_elements": [1.0, 0.0],
                "current_dc_offset_by_port": {"1": 0.0},
                "current_intermediate_frequency": 10000000.0,
                "current_frame": [1.0, 0.0],
                "current_correction_elements": [1.0, 0.0],
                "chirp_info": None,
                "current_phase": 0.0,
            },
            {
                "waveform_name": "gauss_wf",
                "pulse_name": "OriginPulseName=gaussian",
                "length": 100,
                "timestamp": 216,
                "iq_info": {"isPartOfIq": True, "iqGroupId": 0.0, "isI": False, "isQ": True},
                "element": "analog_1",
                "output_ports": [2],
                "controller": "con1",
                "pulser": {"controllerName": "con1", "pulserIndex": 1.0},
                "current_amp_elements": [1.0, 0.0],
                "current_dc_offset_by_port": {"2": 0.0},
                "current_intermediate_frequency": 10000000.0,
                "current_frame": [0.0, 1.0],
                "current_correction_elements": [0.0, 1.0],
                "chirp_info": None,
                "current_phase": 0.0,
            },
        ],
        "digital_waveforms": [
            {
                "waveform_name": "ON",
                "pulse_name": "OriginPulseName=gaussian",
                "length": 100,
                "timestamp": 204,
                "iq_info": {"isPartOfIq": True, "iqGroupId": 0.0, "isI": True, "isQ": False},
                "element": "analog_1",
                "output_ports": [1],
                "controller": "con1",
                "pulser": {"controllerName": "con1", "pulserIndex": 0.0},
            },
            {
                "waveform_name": "ON",
                "pulse_name": "OriginPulseName=gaussian",
                "length": 100,
                "timestamp": 204,
                "iq_info": {"isPartOfIq": True, "iqGroupId": 0.0, "isI": False, "isQ": True},
                "element": "analog_1",
                "output_ports": [1],
                "controller": "con1",
                "pulser": {"controllerName": "con1", "pulserIndex": 1.0},
            },
        ],
        "adc_acquisitions": [],
    }

    if waveform_report is not None:
        assert waveform_report.to_dict() == ref_dict
