import pathlib
import shutil
from pprint import pprint

from qm.octave.calibration_db import CalibrationDB, load_from_calibration_db


def test_load_from_calibration_db(tmp_path):
    current_path = pathlib.Path(__file__).parent.resolve()
    file_location = f"{current_path.absolute()}/resources/calibration_db.json"
    shutil.copyfile(file_location, f"{tmp_path}/calibration_db.json")
    db = CalibrationDB(tmp_path)

    wf_amp = 0.05
    lo_frequency = 10e9
    if_frequency = 60e6
    measure_length = 400

    qua_config = {
        'version': 1,
        'controllers': {
            'con1': {
                'type': 'opx1',
                'analog_outputs': {
                    i + 1: {'offset': 0.0} for i in range(10)
                },
                'analog_inputs': {
                    1: {'offset': 0.0},
                    2: {'offset': 0.0},
                },
                'digital_outputs': {
                    i: {} for i in range(1, 11)
                }
            },
        },

        'elements': {
            'qe1': {
                'mixInputs': {
                    'I': ('con1', 1),
                    'Q': ('con1', 2),
                    'lo_frequency': lo_frequency,
                    'mixer': 'octave_oct1_1'
                },
                'intermediate_frequency': if_frequency,
                'operations': {
                    'pulse': 'pulse',
                    'measure': 'measure_pulse'
                },
                'time_of_flight': 212,
                'smearing': 0,
                'outputs': {
                    'out1': ('con1', 1),
                }
            },
            'qe2': {
                'mixInputs': {
                    'I': ('con1', 3),
                    'Q': ('con1', 4),
                    'lo_frequency': lo_frequency,
                    'mixer': 'octave_oct1_2'
                },
                'intermediate_frequency': if_frequency,
                'operations': {
                    'pulse': 'pulse',
                    'measure': 'measure_pulse'
                },
            },
            'qe3': {
                'mixInputs': {
                    'I': ('con1', 5),
                    'Q': ('con1', 6),
                    'lo_frequency': lo_frequency,
                    'mixer': 'octave_oct1_3'
                },
                'intermediate_frequency': if_frequency,
                'operations': {
                    'pulse': 'pulse',
                    'measure': 'measure_pulse'
                },
            },
            'qe4': {
                'mixInputs': {
                    'I': ('con1', 7),
                    'Q': ('con1', 8),
                    'lo_frequency': lo_frequency,
                    'mixer': 'octave_oct1_4'
                },
                'intermediate_frequency': if_frequency,
                'operations': {
                    'pulse': 'pulse',
                    'measure': 'measure_pulse'
                },
            },
            'qe5': {
                'mixInputs': {
                    'I': ('con1', 9),
                    'Q': ('con1', 10),
                    'lo_frequency': lo_frequency,
                    'mixer': 'octave_oct1_5'
                },
                'intermediate_frequency': if_frequency,
                'operations': {
                    'pulse': 'pulse',
                    'measure': 'measure_pulse'
                },
            },

        },
        'pulses': {
            'measure_pulse': {
                'operation': 'measure',
                'length': measure_length,
                'waveforms': {
                    'I': 'wf1',
                    'Q': 'wf0',
                },
                'integration_weights': {
                    'integ_w_cos': 'integW1_I',
                    'integ_w_sin': 'integW1_Q',
                },
                'digital_marker': 'marker1'
            },
            'pulse': {
                'operation': 'control',
                'length': 1000,
                'waveforms': {
                    'I': 'wf1',
                    'Q': 'wf0',
                },
            },
        },
        'integration_weights': {
            'integW1_I': {
                'cosine': [0.125] * measure_length,
                'sine': [0.0] * measure_length,
            },
            'integW1_Q': {
                'cosine': [0.0] * measure_length,
                'sine': [0.125] * measure_length,
            },
        },
        'digital_waveforms': {
            'marker1': {'samples': [(1, 0)]}
        },
        'waveforms': {
            'wf1': {
                'type': 'constant',
                'sample': wf_amp
            },
            'wf0': {
                'type': 'constant',
                'sample': 0.0
            },
        },
        'mixers': {
            'octave_oct1_1': [
                {'intermediate_frequency': if_frequency, 'lo_frequency': lo_frequency,
                 'correction': [1.0, 0.0, 0.0, 1.0]}],
            'octave_oct1_2': [
                {'intermediate_frequency': if_frequency, 'lo_frequency': lo_frequency,
                 'correction': [1.0, 0.0, 0.0, 1.0]}],
            'octave_oct1_3': [
                {'intermediate_frequency': if_frequency, 'lo_frequency': lo_frequency,
                 'correction': [1.0, 0.0, 0.0, 1.0]}],
            'octave_oct1_4': [
                {'intermediate_frequency': if_frequency, 'lo_frequency': lo_frequency,
                 'correction': [1.0, 0.0, 0.0, 1.0]}],
            'octave_oct1_5': [
                {'intermediate_frequency': if_frequency, 'lo_frequency': lo_frequency,
                 'correction': [1.0, 0.0, 0.0, 1.0]}]
        },

    }
    assert qua_config["mixers"]["octave_oct1_1"][0]["correction"] == [1.0, 0.0, 0.0, 1.0]
    assert qua_config["mixers"]["octave_oct1_1"][0]["lo_frequency"] == lo_frequency
    assert qua_config["mixers"]["octave_oct1_1"][0]["intermediate_frequency"] == if_frequency

    assert qua_config["controllers"]["con1"]["analog_outputs"][1]["offset"] == 0
    assert qua_config["controllers"]["con1"]["analog_outputs"][2]["offset"] == 0
    pprint(qua_config)
    load_from_calibration_db(qua_config, db)
    pprint(qua_config)
    found = False
    for entry in qua_config["mixers"]["octave_oct1_1"]:
        if entry["intermediate_frequency"] == if_frequency and entry["lo_frequency"] == lo_frequency:
            assert entry["correction"] == [
                0.969180250393013,
                0.017163061342150218,
                0.0160913848534256,
                1.0337270682799342
            ]
            found = True

    assert found

    assert qua_config["controllers"]["con1"]["analog_outputs"][1]["offset"] == -0.043212890625
    assert qua_config["controllers"]["con1"]["analog_outputs"][2]["offset"] == 0.039306640625
