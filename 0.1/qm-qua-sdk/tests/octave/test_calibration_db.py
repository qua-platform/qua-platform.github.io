import pytest

from qm.octave.calibration_db import (
    CalibrationResult,
    CalibrationDB,
    load_from_calibration_db,
    octave_output_mixer_name,
)
from tests_against_server.stream_processing.configuration_basic import IQ_imbalance


def test_save_and_load(tmp_path):
    db = CalibrationDB(tmp_path)
    orig = CalibrationResult(
        [1, 2, 3, 4],
        0.15,
        -0.03,
        0.1,
        0.2,
        0.3,
        octave_output_mixer_name("octave1", 1),
        {},
    )

    db.update_calibration_data(orig)
    assert db.get(octave_output_mixer_name("octave1", 1), 0.1, 0.2) == orig
    del db

    db = CalibrationDB(tmp_path)
    assert db.get(octave_output_mixer_name("octave1", 1), 0.1, 0.2) == orig
    assert db[octave_output_mixer_name("octave1", 1), 0.1, 0.2] == orig

    second = CalibrationResult(
        [1, 2, 3, 4],
        0.15,
        -0.03,
        0.1,
        0.3,
        0.3,
        octave_output_mixer_name("octave1", 1),
        {},
    )
    db.update_calibration_data([second])
    calibrations_for_lo = db.get_for_lo_frequency(
        octave_output_mixer_name("octave1", 1), 0.1
    )
    assert orig in calibrations_for_lo
    assert second in calibrations_for_lo


def test_save_and_get_all(tmp_path):
    db = CalibrationDB(tmp_path)
    mixer_name = octave_output_mixer_name("octave1", 1)
    # adding values for different combination of the same lo and if freqs:
    # different if and lo
    # same if and different lo
    # different if and same lo
    orig = [CalibrationResult(
        [1, 2, 3, 4],
        0.15 * i,
        -0.03 * i,
        1.5e9 * i,
        50e6 + i * 1e6,
        0.3,
        mixer_name,
        {},
    ) for i in range(1, 15)] + [CalibrationResult(
        [1, 2, 3, 4],
        0.15 * i,
        -0.03 * i,
        1.6e9 * i,
        60e6 + i * 1e6,
        0.3,
        mixer_name,
        {},
    ) for i in range(1, 15)] + [CalibrationResult(
        [1, 2, 3, 4],
        0.15 * i,
        -0.03 * i,
        1.5e9 * i,
        60e6 + i * 1e6,
        0.3,
        mixer_name,
        {},
    ) for i in range(1, 15)]

    # trying to add twice to make sure it replaced
    db.update_calibration_data(orig)
    db.update_calibration_data(orig)
    assert len(set([(r.lo_frequency, r.if_frequency) for r in orig])) == 42
    assert len(db.get_all(mixer_name)) == 42
    assert len(db.get_all_or_default(mixer_name)) == 42
    assert db.get_all_or_default("blah") == []
    assert len(db.get_for_lo_frequency(mixer_name, 1.5e9)) == 2
    assert db.get(mixer_name, 1.5e9 * 2, 52e6) == orig[1]
    with pytest.raises(AttributeError):
        db.get(mixer_name, 1.5e9 * 2, 152e6)


def test_load_from_calibration_db(tmp_path):
    mixer_name = octave_output_mixer_name("octave1", 1)
    config = {
        "version": 1,
        "controllers": {
            "con1": {
                "type": "opx1",
                "analog_outputs": {
                    1: {"offset": 0.05},
                    2: {"offset": -0.05},
                    3: {"offset": -0.024},
                    4: {"offset": 0.115},  # Readout resonator
                },
                "digital_outputs": {
                    1: {},
                },
                "analog_inputs": {
                    1: {"offset": +0.0},
                },
            }
        },
        "elements": {
            "qubit": {
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 2e9,
                    "mixer": mixer_name,
                },
                "intermediate_frequency": 30e6,
                "operations": {
                    "X": "XPulse",
                },
            },
            "rr": {
                "mixInputs": {
                    "I": ("con1", 3),
                    "Q": ("con1", 4),
                    "lo_frequency": 2e9,
                    "mixer": "mixer_RR",
                },
                "intermediate_frequency": 30e6,
                "operations": {
                    "readout": "readout_pulse",
                },
                "outputs": {"out1": ("con1", 1)},
                "time_of_flight": 28,
                "smearing": 0,
            },
        },
        "pulses": {
            "XPulse": {
                "operation": "control",
                "length": 1000,
                "waveforms": {"I": "gauss_wf", "Q": "zero_wf"},
            },
            "readout_pulse": {
                "operation": "measurement",
                "length": 1000,
                "waveforms": {"I": "readout_wf", "Q": "zero_wf"},
                "integration_weights": {
                    "integW1": "integW1",
                    "integW2": "integW2",
                },
                "digital_marker": "ON",
            },
        },
        "waveforms": {
            "zero_wf": {"type": "constant", "sample": 0.0},
            "gauss_wf": {"type": "arbitrary", "samples": [0] * 1000},
            "readout_wf": {"type": "constant", "sample": 0.3},
        },
        "digital_waveforms": {
            "ON": {"samples": [(1, 0)]},
        },
        "integration_weights": {
            "integW1": {
                "cosine": [1.0] * int(1000 / 4),
                "sine": [0.0] * int(1000 / 4),
            },
            "integW2": {
                "cosine": [0.0] * int(1000 / 4),
                "sine": [1.0] * int(1000 / 4),
            },
        },
        "mixers": {
            "mixer_qubit": [
                {
                    "intermediate_frequency": 31e6,
                    "lo_frequency": 3e9,
                    "correction": IQ_imbalance(0.0, 0.0),
                }
            ],
            mixer_name: [
                {
                    "intermediate_frequency": 30e6,
                    "lo_frequency": 2e9,
                    "correction": [0.0, 0.1, 0.2, 0.3],
                },
                {
                    "intermediate_frequency": 31e6,
                    "lo_frequency": 3e9,
                    "correction": [0.0, 0.1, 0.2, 0.3],
                },
            ],
        },
    }
    db = CalibrationDB(tmp_path)
    orig = CalibrationResult(
        [1, 2, 3, 4], 0.15, -0.03, 2e9, 30e6, 0.3,
        octave_output_mixer_name("octave1", 1), {}
    )

    db.update_calibration_data(orig)
    assert config["mixers"][mixer_name][0]["correction"] == [0.0, 0.1, 0.2, 0.3]
    assert config["mixers"][mixer_name][0]["lo_frequency"] == 2e9
    assert config["mixers"][mixer_name][0]["intermediate_frequency"] == 30e6
    assert config["mixers"][mixer_name][1]["correction"] == [0.0, 0.1, 0.2, 0.3]
    assert config["mixers"][mixer_name][1]["lo_frequency"] == 3e9
    assert config["mixers"][mixer_name][1]["intermediate_frequency"] == 31e6

    assert config["controllers"]["con1"]["analog_outputs"][1]["offset"] == 0.05
    assert config["controllers"]["con1"]["analog_outputs"][2]["offset"] == -0.05

    load_from_calibration_db(config, db)

    assert config["mixers"][mixer_name][0]["correction"] == [1, 2, 3, 4]
    assert config["mixers"][mixer_name][0]["lo_frequency"] == 2e9
    assert config["mixers"][mixer_name][0]["intermediate_frequency"] == 30e6
    assert config["mixers"][mixer_name][1]["correction"] == [0.0, 0.1, 0.2, 0.3]
    assert config["mixers"][mixer_name][1]["lo_frequency"] == 3e9
    assert config["mixers"][mixer_name][1]["intermediate_frequency"] == 31e6

    assert config["controllers"]["con1"]["analog_outputs"][1]["offset"] == 0.15
    assert config["controllers"]["con1"]["analog_outputs"][2]["offset"] == -0.03
