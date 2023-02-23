from unittest.mock import MagicMock

import pytest

from qm.octave import OctaveOutput, OctaveLOSource
from qm.octave.calibration_db import CalibrationResult
import qm.octave.octave_config as config

DEFAULT_CONNECTIONS = {
    ('con1', 1): ('octave1', 'I1'),
    ('con1', 2): ('octave1', 'Q1'),
    ('con1', 3): ('octave1', 'I2'),
    ('con1', 4): ('octave1', 'Q2'),
    ('con1', 5): ('octave1', 'I3'),
    ('con1', 6): ('octave1', 'Q3'),
    ('con1', 7): ('octave1', 'I4'),
    ('con1', 8): ('octave1', 'Q4'),
    ('con1', 9): ('octave1', 'I5'),
    ('con1', 10): ('octave1', 'Q5')
}


def test_octave_config_opx():
    octave_config = config.QmOctaveConfig()
    octave_config.add_device_info("octave1", "127.0.0.1", 333)
    octave_config.set_opx_octave_mapping([("con1", "octave1")])
    default = octave_config.get_opx_octave_port_mapping()
    assert default == DEFAULT_CONNECTIONS
    octave_config.add_opx_octave_port_mapping(
        {("con1", 1): ("octave1", "I5"), ("con1", 2): ("octave1", "Q5")}
    )
    new_conns = octave_config.get_opx_octave_port_mapping()
    assert new_conns == {
        ("con1", 1): ("octave1", "I5"),
        ("con1", 2): ("octave1", "Q5"),
        ('con1', 3): ('octave1', 'I2'),
        ('con1', 4): ('octave1', 'Q2'),
        ('con1', 5): ('octave1', 'I3'),
        ('con1', 6): ('octave1', 'Q3'),
        ('con1', 7): ('octave1', 'I4'),
        ('con1', 8): ('octave1', 'Q4'),
        ('con1', 9): ('octave1', 'I5'),
        ('con1', 10): ('octave1', 'Q5')
    }

    iq = octave_config.get_opx_iq_ports(("octave1", 2))
    assert iq == [("con1", 3), ("con1", 4)]
    assert iq[0][0] == "con1"

    with pytest.raises(
        KeyError,
        match="Could not find opx connections to port 'I1' of octave 'octave1'"
    ):
        octave_config.get_opx_iq_ports(("octave1", 1))


def test_overriding_opx_octave_connections(monkeypatch):
    logger_mock = MagicMock()
    monkeypatch.setattr(config, "logger", logger_mock)
    octave_config = config.QmOctaveConfig()
    octave_config.add_opx_octave_port_mapping(
        {("con1", 1): ("octave1", "I5"), ("con1", 2): ("octave1", "Q5")}
    )
    logger_mock.warning.assert_not_called()
    octave_config.set_opx_octave_mapping([("con1", "octave1")])
    logger_mock.warning.assert_called_once()


def test_octave_config_opx_bad_connections():
    octave_config = config.QmOctaveConfig()

    with pytest.raises(ValueError):
        octave_config.add_opx_octave_port_mapping(
            {("con1", 1): ("octave1", "Iqq1"), ("con1", 2): ("octave1", "Q1")}
        )


def test_octave_config_calibration_db(tmpdir):
    octave_config = config.QmOctaveConfig()
    octave_config.set_calibration_db(tmpdir)
    result = CalibrationResult([0.1, 0.2, 0.3, 0.4], 0.01, -0.01, 2e9, 50e6, 6.0,
                               "mixer", {})
    octave_config.calibration_db.update_calibration_data(result)

    octave_config2 = config.QmOctaveConfig()
    octave_config2.set_calibration_db(tmpdir)
    query = octave_config2.calibration_db.get_all("mixer")
    assert len(query) == 1
    assert query[0] == result


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
def test_octave_config_loop_backs(synth: OctaveOutput, lo_source: OctaveLOSource):
    octave_config = config.QmOctaveConfig()
    octave_config.add_device_info("octave1", "127.0.0.1", 333)
    octave_config.add_lo_loopback("octave1", synth, "octave1", lo_source)
    loop_backs = octave_config.get_lo_loopbacks_by_octave("octave1")
    assert loop_backs == {lo_source: synth}
