import types

import pytest

from qm.serialization.generate_qua_script import (
    generate_qua_script,
    CONFIG_ERROR,
    LOADED_CONFIG_ERROR,
    SERIALIZATION_NOT_COMPLETE,
    SERIALIZATION_VALIDATION_ERROR,
    _make_compact_string_from_list,
)
from qm.qua import program, play
from .sample_config import config as imported_config


def assert_serialization_worked(result: str):
    assert CONFIG_ERROR not in result
    assert LOADED_CONFIG_ERROR not in result
    assert SERIALIZATION_NOT_COMPLETE not in result
    assert SERIALIZATION_VALIDATION_ERROR not in result


def test_simple_config():
    with program() as simple_program:
        play("pulse", "element")

    valid_config = {
        "version": "1",
        "elements": {"el1": {"singleInput": {"port": ("con1", 1)}, "oscillator": "osc"}},
        "integration_weights": {
            "long_integW1": {"cosine": [1.0] * 50, "sine": [0.0] * 50},
        },
    }

    result = generate_qua_script(simple_program, valid_config)
    print(result)

    assert_serialization_worked(result)

    generated_mod = types.ModuleType("gen")
    exec(result, generated_mod.__dict__)
    gen_config = generated_mod.config

    assert gen_config == valid_config


def test_config_with_apo_in_name():
    with program() as simple_program:
        play("pulse", "element'")

    valid_config = {
        "version": "1",
        "elements": {"element'": {"singleInput": {"port": ("con1", 1)}, "oscillator": "osc"}},
        "integration_weights": {
            "long_integW1": {"cosine": [1.0] * 50, "sine": [0.0] * 50},
        },
    }

    result = generate_qua_script(simple_program, valid_config)
    print(result)

    assert_serialization_worked(result)

    generated_mod = types.ModuleType("gen")
    exec(result, generated_mod.__dict__)
    gen_config = generated_mod.config

    assert gen_config == valid_config


def test_bad_config():
    with program() as simple_program:
        play("pulse", "element")

    valid_config = {
        "version": "1",
        "elementsfds": {},
    }
    with pytest.raises(RuntimeError, match="bad config"):
        generate_qua_script(simple_program, valid_config)


def test_serialize_in_prog():
    with program() as simple_program:
        play("pulse", "element")

        with pytest.raises(RuntimeError, match="inside the qua program scope"):
            generate_qua_script(simple_program)


def test_complex_config():
    with program() as simple_program:
        play("pulse", "element")

    valid_config = imported_config

    result = generate_qua_script(simple_program, valid_config)
    print(result)

    assert_serialization_worked(result)

    generated_mod = types.ModuleType("gen")
    exec(result, generated_mod.__dict__)
    gen_config = generated_mod.config

    assert gen_config == valid_config


@pytest.mark.parametrize("i", range(0, 11))
def test_compact_list(i: int):
    l = [0.0] * (i - 1) + [1.0] + [0.0] * (10 - i)
    compact = _make_compact_string_from_list(l)
    assert l == eval(compact)


@pytest.mark.parametrize(
    ("input_list", "result"),
    [
        ([1], "[1]"),
        ([1] * 10, "[1] * 10"),
        ([1, 2, 3], "[1, 2, 3]"),
        ([3, 3], "[3] * 2"),
    ],
)
def test_compact_list_simple_examples(input_list, result):
    compact = _make_compact_string_from_list(input_list)
    assert compact == result


def test_config_arb_integration():
    with program() as simple_program:
        play("pulse", "element")

    valid_config = {
        "version": "1",
        "elements": {"el1": {"singleInput": {"port": ("con1", 1)}, "oscillator": "osc"}},
        "integration_weights": {
            "long_integW1": {
                "cosine": [(1.0, 4), (2.0, 4), (1.0, 4)],
                "sine": [(1.0, 4), (2.0, 4), (1.0, 4)],
            },
        },
    }

    result = generate_qua_script(simple_program, valid_config)
    print(result)

    assert_serialization_worked(result)

    generated_mod = types.ModuleType("gen")
    exec(result, generated_mod.__dict__)
    gen_config = generated_mod.config

    assert gen_config == valid_config


def test_config_multiple_correction_matrices():
    with program() as simple_program:
        play("pulse", "element")

    valid_config = {
        "version": "1",
        "elements": {"el1": {"singleInput": {"port": ("con1", 1)}, "oscillator": "osc"}},
        "integration_weights": {
            "long_integW1": {
                "cosine": [(1.0, 4), (2.0, 4), (1.0, 4)],
                "sine": [(1.0, 4), (2.0, 4), (1.0, 4)],
            },
        },
        "mixers": {
            "readout_mixer": [
                {
                    "correction": [-0.26420509515754076, 0.9518366653717653, 0.975444999933659, -0.270758154633349],
                    "intermediate_frequency": 104650000,
                    "lo_frequency": 7800000000,
                }
            ],
            "transmon_mixer": [
                {
                    "correction": [0.80328247406241, 0.12236657737503598, 0.18533754517572806, 1.2166590340197356],
                    "intermediate_frequency": 81298534,
                    "lo_frequency": 4200000000,
                },
                {"correction": [1, 0, 0, 1], "intermediate_frequency": 214126117, "lo_frequency": 4200000000},
                {
                    "correction": [0.80328247406241, 0.12236657737503598, 0.18533754517572806, 1.2166590340197356],
                    "intermediate_frequency": 75125125,
                    "lo_frequency": 4200000000,
                },
                {"correction": [1, 0, 0, 1], "intermediate_frequency": 74294668, "lo_frequency": 4200000000},
            ],
        },
    }

    result = generate_qua_script(simple_program, valid_config)
    print(result)

    assert_serialization_worked(result)

    generated_mod = types.ModuleType("gen")
    exec(result, generated_mod.__dict__)
    gen_config = generated_mod.config

    assert gen_config == valid_config


def test_config_with_digital_input():
    with program() as simple_opd_prog:
        play("pulse", "element")

    valid_digital_config = {
        "version": 1,
        "controllers": {
            "con1": {
                "digital_inputs": {
                    "1": {"deadtime": 4, "polarity": "RISING", "threshold": 0.1},
                    "2": {"deadtime": 16, "polarity": "FALLING", "threshold": 0.1},
                }
            }
        },
    }

    result = generate_qua_script(simple_opd_prog, valid_digital_config)
    print(result)

    assert_serialization_worked(result)

    generated_mod = types.ModuleType("gen")
    exec(result, generated_mod.__dict__)
    gen_config = generated_mod.config

    assert gen_config == valid_digital_config


def test_failing_config_with_digital_input():
    with program() as simple_opd_prog:
        play("pulse", "element")

    invalid_digital_config = {
        "version": 1,
        "controllers": {
            "con1": {
                "digital_inputs": {
                    "1": {"deadtime": 4, "polarity": "ABC", "threshold": 0.1},
                    "2": {"deadtime": 16, "polarity": "FALLING", "threshold": 0.1},
                }
            }
        },
    }

    with pytest.raises(Exception):
        result = generate_qua_script(simple_opd_prog, invalid_digital_config)
        print(result)
        assert_serialization_worked(result)

        generated_mod = types.ModuleType("gen")
        exec(result, generated_mod.__dict__)
        gen_config = generated_mod.config

        assert gen_config == invalid_digital_config


def test_list_instead_of_tuple_config():
    with program() as simple_program:
        play("pulse", "element")

    valid_config = {
        "version": "1",
        "elements": {"el1": {"singleInput": {"port": ["con1", 1]}, "oscillator": "osc"}},
        "integration_weights": {
            "long_integW1": {"cosine": [1.0] * 50, "sine": [0.0] * 50},
        },
    }

    result = generate_qua_script(simple_program, valid_config)
    print(result)

    assert_serialization_worked(result)

    generated_mod = types.ModuleType("gen")
    exec(result, generated_mod.__dict__)
    gen_config = generated_mod.config

    assert gen_config == valid_config
