from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from qm.qua import Math
from qm import LoopbackInterface
from qm import SimulationConfig
import numpy as np
import matplotlib.pyplot as plt

################
# configuration:
################

# The configuration is our way to describe your setup.

config = {

    'version': 1,

    'controllers': {

        "con1": {
            'type': 'opx1',
            'analog_outputs': {
                1: {'offset': +0.0},
                2: {'offset': +0.},
                3: {'offset': +0.},  #

            },
            'digital_outputs': {
                1: {},
            },
            'analog_inputs': {
                1: {'offset': +0.0},
            }
        }
    },

    'elements': {

        "drivingElem": {
            "singleInput": {
                "port": ("con1", 1)
            },
            'intermediate_frequency': 1e6,
            'operations': {
                'rabiOp': "constPulse",
            },
        },
        "qubitSimElem": {
            "singleInput": {
                "port": ("con1", 3)
            },
            'intermediate_frequency': 0,
            'operations': {
                'shineOp': "constPulse",
            },
        },
        "measElem": {
            "singleInput": {
                "port": ("con1", 2)
            },
            'outputs': {
                'output1': ('con1', 1)
            },
            'intermediate_frequency': 1e6,
            'operations': {
                'readoutOp': 'readoutPulse',

            },
            'time_of_flight': 180,
            'smearing': 0
        },
    },

    "pulses": {
        "onPulse": {
            'operation': 'control',
            'length': 1000,
            'waveforms': {
                'single': 'const_wf'
            },
            'digital_marker': 'ON',
        },
        "rabiPulse": {
            'operation': 'control',
            'length': 1000,
            'waveforms': {
                'single': 'const_wf'
            }
        },
        "constPulse": {
            'operation': 'control',
            'length': 1000,
            'waveforms': {
                'single': 'const_wf'
            }
        },
        'readoutPulse': {
            'operation': 'measure',
            'length': 1000,
            'waveforms': {
                'single': 'const_wf'
            },
            'digital_marker': 'ON',
            'integration_weights': {
                'x': 'xWeights',
                'y': 'yWeights'}
        },
    },

    "waveforms": {
        'const_wf': {
            'type': 'constant',
            'sample': 0.2
        },
    },
    'digital_waveforms': {
        'ON': {
            'samples': [(1, 0)]
        },
    },
    'integration_weights': {
        'xWeights': {
            'cosine': [1.0] * 1000,
            'sine': [0.0] * 1000
        },
        'yWeights': {
            'cosine': [0.0] * 1000,
            'sine': [1.0] * 1000
        }
    }
}

# Open communication with the server.
QMm = QuantumMachinesManager()

# Create a quantum machine based on the configuration.

QM1 = QMm.open_qm(config)

with program() as myFirstProgram:
    d = declare(int)
    a = declare(fixed, value=0.0)
    I=declare(fixed,value=0)
    rabi_stream = declare_stream(adc_trace=True)
    param_stream = declare_stream()
    with for_(d, 1e3, d < 1e4, d + 1e3):
        play('rabiOp', 'drivingElem', duration=d)
        align('measElem', 'qubitSimElem', 'drivingElem')
        play('shineOp' * amp(Math.sin(a)), 'qubitSimElem')
        # measure('readoutOp', 'measElem', None,integration.full('x',I))
        measure('readoutOp', 'measElem', rabi_stream)
        # save(I,rabi_stream)
        save(d,param_stream)
        assign(a, a + 0.8)
        wait(1000, 'drivingElem')
    with stream_processing():
        rabi_stream.input1().map(FUNCTIONS.average()).save_all('rabi_data')
        # rabi_stream.input1().map(FUNCTIONS.average()).save('rabi_data')
        param_stream.save_all('param_data')

job = QM1.simulate(myFirstProgram,
                   SimulationConfig(int(8e4), simulation_interface=LoopbackInterface([("con1", 3, "con1", 1)])))

samples = job.get_simulated_samples()

samples.con1.plot()

res = job.result_handles
rabiData = res.rabi_data.fetch_all()['value']
durData=res.param_data.fetch_all()['value']

plt.figure()
plt.plot(durData/1000,rabiData/4096,'o')
plt.xlabel('$t[\mu s]$')
plt.ylabel('$input [V]$')
plt.show()
