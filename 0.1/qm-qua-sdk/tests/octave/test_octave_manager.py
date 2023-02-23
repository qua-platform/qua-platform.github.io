from unittest.mock import MagicMock

import pytest

from qm.octave import QmOctaveConfig, OctaveOutput, OctaveLOSource
import qm


@pytest.fixture()
def mock_octave_sdk(monkeypatch):
    mid_level_mock = MagicMock()

    sdk_enums = {
        "sdk_OctaveLOSource": MagicMock(),
        "sdk_OctaveOutput": MagicMock(),
        "sdk_RFInputRFSource": MagicMock(),
        "sdk_RFOutputMode": MagicMock(),
        "sdk_RFInputLOSource": MagicMock(),
        "sdk_ClockType": MagicMock(),
        "sdk_ClockFrequency": MagicMock()
    }

    monkeypatch.setattr("qm.octave.octave_manager.Octave", mid_level_mock)
    monkeypatch.setattr("qm.octave.octave_manager.OCTAVE_SDK_LOADED", True)

    for enum_name, mock in sdk_enums.items():
        monkeypatch.setattr(f"qm.octave.enums.{enum_name}", mock)

    yield mid_level_mock, sdk_enums


@pytest.mark.parametrize(
    "synth",
    [
        OctaveOutput.Synth1,
        OctaveOutput.Synth2,
        OctaveOutput.Synth3
    ]
)
@pytest.mark.parametrize(
    "lo_source",
    [
        OctaveLOSource.LO1,
        OctaveLOSource.LO2,
        OctaveLOSource.LO3,
        OctaveLOSource.LO4,
        OctaveLOSource.LO5
    ]
)
def test_octave_manager_loop_backs(monkeypatch, synth, lo_source, mock_octave_sdk):
    octave_config = QmOctaveConfig()
    octave_config.add_device_info("octave1", "127.0.0.1", 333)
    octave_config.add_lo_loopback("octave1", synth, "octave1", lo_source)

    qmm_mock = MagicMock()
    octave_mid_level_mock, _ = mock_octave_sdk

    manager = qm.octave.octave_manager.OctaveManager(config=octave_config, qmm=qmm_mock)
    octave_mid_level_mock.assert_called_with(
        host="127.0.0.1",
        port=333,
        port_mapping={lo_source.to_sdk(): synth.to_sdk()},
        octave_name="octave1",
        fan=octave_config.fan
    )
