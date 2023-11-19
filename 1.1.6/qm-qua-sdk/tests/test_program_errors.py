from qm.qua import *
import pytest


def test_used_array_in_scalar_places():
    with program():
        res_vec = declare(int, size=1)
        with pytest.raises(Exception, match="invalid expression: '.*' is not a scalar expression"):
            save(res_vec, "res")

        with pytest.raises(Exception, match="invalid expression: '.*' is not a scalar expression"):
            ramp(res_vec)


def test_logical_errors():
    with program():
        a = declare(bool)
        with if_(~a):
            save(a, "res")

        with pytest.raises(Exception, match="Attempted to use a Python logical operator on a QUA variable"):
            with if_(not a):
                save(a, "res")


def test_save_expression():
    with program():
        i = declare(int)
        f = declare(fixed)

        with pytest.raises(
            QmQuaException,
            match="library expression .* is not a valid save source.",
        ):
            save(Cast.to_fixed(i), "i")

        with pytest.raises(
            QmQuaException,
            match="library expression .* is not a valid save source.",
        ):
            save(Math.abs(f), "f")
