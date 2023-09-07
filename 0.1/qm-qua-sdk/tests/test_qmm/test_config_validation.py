import pytest

from qm.exceptions import ConfigValidationException


def test_config_validation(qmm_mock, qua_bare_config):
    qmm_mock.validate_qua_config(qua_bare_config)


def test_wrong_key(qmm_mock, qua_bare_config):
    qua_bare_config["controllers"]["con1"]["wrong_key"] = 2
    with pytest.raises(ConfigValidationException):
        qmm_mock.validate_qua_config(qua_bare_config)


def test_wrong_value(qmm_mock, qua_bare_config):
    qua_bare_config["controllers"]["con1"]["analog_inputs"][1]["offset"] = "not a number"
    with pytest.raises(ConfigValidationException):
        qmm_mock.validate_qua_config(qua_bare_config)
