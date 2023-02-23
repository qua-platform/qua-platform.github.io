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
}

# Open communication with the server.
QMm = QuantumMachinesManager()

# Create a quantum machine based on the configuration.

QM1 = QMm.open_qm(config)

with program() as rabiProgram:
    d=declare(int)
    a=declare(fixed,value=0.0)
    rabi_stream = declare_stream()
    with for_(d,1e3,d<1e4,d+1e3):
        play('rabiOp','drivingElem',duration=d)
        align('measElem','qubitSimElem','drivingElem')
        play('shineOp'*amp(Math.sin(a)),'qubitSimElem')
        measure('readoutOp', 'measElem',rabi_stream)
        assign(a, a + 0.8)
        wait(1000,'drivingElem')
    with stream_processing():
        rabi_stream.input1().with_timestamps().save_all('rabi_data')

job = QM1.simulate(rabiProgram,
                   SimulationConfig(int(8e4), simulation_interface=LoopbackInterface([("con1", 3, "con1", 1)])))

samples = job.get_simulated_samples()

samples.con1.plot()

res=job.result_handles
rabiData=res.rabi_data.fetch_all()['value']
plt.figure()
plt.plot(rabiData/4096)
plt.show()
