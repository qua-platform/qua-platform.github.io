import numpy as np

from qm.octave._calibration_analysis import ImageDataAnalysisResult, FitResult
from qm.octave.calibration_db import CalibrationDB
from qm.octave.octave_mixer_calibration import LOFrequencyCalibrationResult, LOFrequencyDebugData, ImageResult


GAIN = 3.14


def test_save_and_load(tmp_path):
    lo_freq = 12
    calibration_result = {
        (lo_freq, GAIN): LOFrequencyCalibrationResult(
            debug=LOFrequencyDebugData(tuple(), None, [], []),
            i0=0.1,
            q0=0.2,
            dc_gain=0.5,
            dc_phase=0.6,
            temperature=0.7,
            image={},
        )
    }

    db = CalibrationDB(tmp_path)
    db.update_calibration_result(calibration_result, ("some_octave", 1))
    query_result = db.get_lo_cal(("some_octave", 1), lo_freq, GAIN)
    assert query_result.i0 == 0.1
    assert query_result.q0 == 0.2
    del db

    db = CalibrationDB(tmp_path)
    new_query_result = db.get_lo_cal(("some_octave", 1), lo_freq, GAIN)
    assert new_query_result == query_result

    new_calibration_result = {
        (lo_freq, GAIN): LOFrequencyCalibrationResult(
            debug=LOFrequencyDebugData(tuple(), None, [], []),
            i0=-0.1,
            q0=-0.2,
            dc_gain=0.5,
            dc_phase=0.6,
            temperature=0.7,
            image={},
        )
    }

    db.update_calibration_result(new_calibration_result, ("some_octave", 1))
    new_query = db.get_lo_cal(("some_octave", 1), lo_freq, GAIN)
    assert new_query.i0 == -0.1
    assert new_query.q0 == -0.2


def test_save_and_get_all(tmp_path):
    db = CalibrationDB(tmp_path)
    octave_port = ("octave1", 1)

    calibration_result = {
        (1.5e9 * i, GAIN): LOFrequencyCalibrationResult(
            debug=LOFrequencyDebugData(tuple(), None, [], []),
            i0=0.15 * i,
            q0=-0.03 * i,
            dc_gain=0.5,
            dc_phase=0.6,
            temperature=0.7,
            image={
                60e6
                + j
                * 1e6: ImageResult(
                    coarse=ImageDataAnalysisResult(
                        phase=-0.2 * j,
                        gain=-0.1 * j,
                        correction=(0.4, 0.3, 0.2, 0.1),
                        g_scan=np.array([0]),
                        p_scan=np.array([0]),
                        image=np.array([0]),
                        fit=FitResult(np.array([1]), 0, 0, 0, np.array([1])),
                    ),
                    fine=ImageDataAnalysisResult(
                        phase=0.2 * j,
                        gain=0.1 * j,
                        correction=(0.4, 0.3, 0.2, 0.1),
                        g_scan=np.array([0]),
                        p_scan=np.array([0]),
                        image=np.array([0]),
                        fit=FitResult(np.array([1]), 0, 0, 0, np.array([1])),
                    ),
                    prev_result=None,
                )
                for j in range(3)
            },
        )
        for i in range(15)
    }

    # trying to add twice to make sure it replaced
    db.update_calibration_result(calibration_result, octave_port)
    db.update_calibration_result(calibration_result, octave_port)

    assert len(db.get_all_if_cal_for_lo(octave_port, 1.5e9, GAIN)) == 3
    assert db.get_if_cal(octave_port, 1.5e9 * 2, GAIN, 61e6) is not None
    assert db.get_if_cal(octave_port, 1.5e9 * 2, GAIN, 61.45e6) is None
    assert db.get_all_if_cal_for_lo(octave_port, 1.524e9 * 2, GAIN) == {}
