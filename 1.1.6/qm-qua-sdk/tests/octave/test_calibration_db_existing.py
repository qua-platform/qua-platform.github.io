import pathlib
import shutil
from pprint import pprint

from qm import DictQuaConfig
from qm.api.models.capabilities import ServerCapabilities
from qm.grpc.qua_config import QuaConfigMatrix
from qm.octave import QmOctaveConfig
from qm.octave.calibration_db import CalibrationDB
from qm._octaves_container import load_config_from_calibration_db
from qm.program._qua_config_to_pb import load_config_pb


def octave_config() -> QmOctaveConfig:
    _octave_config = QmOctaveConfig()
    _octave_config.add_device_info("oct1", "127.0.0.1", 333)
    return _octave_config


def test_load_from_calibration_db(tmp_path):
    current_path = pathlib.Path(__file__).parent.resolve()
    file_location = f"{current_path.absolute()}/resources/calibration_db.json"
    shutil.copyfile(file_location, f"{tmp_path}/calibration_db.json")
    db = CalibrationDB(str(tmp_path))

    lo_frequency = 10e9
    if_frequency = -71500000.0

    qua_config: DictQuaConfig = {
        "version": 1,
        "controllers": {
            "con1": {
                "type": "opx1",
                "analog_outputs": {i + 1: {"offset": 0.0} for i in range(10)},
                "analog_inputs": {
                    1: {"offset": 0.0},
                    2: {"offset": 0.0},
                },
                "digital_outputs": {i: {} for i in range(1, 11)},
            },
        },
        "elements": {
            "qe1": {
                "mixInputs": {"I": ("con1", 1), "Q": ("con1", 2)},
                "intermediate_frequency": if_frequency,
                "operations": {},
            },
            "qe2": {
                "mixInputs": {"I": ("con1", 3), "Q": ("con1", 4)},
                "intermediate_frequency": if_frequency,
                "operations": {},
            },
            "qe3": {
                "mixInputs": {"I": ("con1", 5), "Q": ("con1", 6)},
                "intermediate_frequency": if_frequency,
                "operations": {},
            },
            "qe4": {
                "mixInputs": {"I": ("con1", 7), "Q": ("con1", 8)},
                "intermediate_frequency": if_frequency,
                "operations": {},
            },
            "qe5": {
                "mixInputs": {"I": ("con1", 9), "Q": ("con1", 10)},
                "intermediate_frequency": if_frequency,
                "operations": {},
            },
        },
        "octaves": {
            "oct1": {
                "connectivity": "con1",
                "RF_outputs": {
                    1: {"LO_frequency": lo_frequency, "gain": 0},
                    2: {"LO_frequency": lo_frequency, "gain": 0},
                    3: {"LO_frequency": lo_frequency, "gain": 0},
                    4: {"LO_frequency": lo_frequency, "gain": 0},
                    5: {"LO_frequency": lo_frequency, "gain": 0},
                },
            }
        },
    }

    assert qua_config["controllers"]["con1"]["analog_outputs"][1]["offset"] == 0
    assert qua_config["controllers"]["con1"]["analog_outputs"][2]["offset"] == 0
    pprint(qua_config)

    capabilities = ServerCapabilities(*[True] * 14 + [0])

    config_after_modification = load_config_from_calibration_db(
        load_config_pb(qua_config), db, octave_config(), capabilities
    )
    found = False
    mixer_name = config_after_modification.v1_beta.elements["qe1"].mix_inputs.mixer
    for entry in config_after_modification.v1_beta.mixers[mixer_name].correction:
        if (
            entry.frequency_double == abs(if_frequency)
            and entry.lo_frequency_double == lo_frequency
            and entry.frequency_negative == (if_frequency < 0)
        ):
            assert entry.correction == QuaConfigMatrix(
                1.0115683443091121, -0.11171006428555381, -0.11324073646574313, 1.0254290428316386
            )
            found = True

    assert found
    analog_outputs = config_after_modification.v1_beta.control_devices["con1"].fems[1].opx.analog_outputs
    assert analog_outputs[1].offset == -0.008240181297692948
    assert analog_outputs[2].offset == 0.028723706805086662
