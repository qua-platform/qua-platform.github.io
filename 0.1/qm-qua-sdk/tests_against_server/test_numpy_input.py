from qm.qua import *
from qm.quantum_machines_manager import QuantumMachinesManager
from qm.exceptions import FailedToExecuteJobException
from tests.simulate.opx_config import create_opx_config
from qm.simulate.interface import SimulationConfig
from qm.simulate import loopback

import numpy as np
import pytest


logger = logging.getLogger(__name__)


i32 = np.int32
u32 = np.uint32
i64 = np.int64
u64 = np.uint64
f32 = np.float32
f64 = np.float64
f128 = np.longfloat
f16 = np.float16

np.set_printoptions(precision=64)


def fixed_arange(start, stop, step, float_type=f32):
    float_array = [x.item() for x in np.arange(start, stop, step, dtype=float_type)]
    return [float_to_fix(x) for x in float_array]


def float_to_fix(number):
    return np.round(number * 2 ** 28) / 2 ** 28


def _run_sim(prog, host_port, vars_to_save):
    qmm = QuantumMachinesManager(**host_port)
    qmm.close_all_quantum_machines()
    job = qmm.simulate(
        create_opx_config(),
        prog,
        SimulationConfig(
            duration=4000, simulation_interface=loopback.LoopbackInterface([])
        ),
    )
    job.result_handles.wait_for_all_values()

    var_vals = {}
    for v in vars_to_save:
        var_vals[v] = [e[0] for e in job.result_handles.get(v).fetch_all()]

    return var_vals


@pytest.mark.parametrize("float_type", [f16, f32, f64, f128])
@pytest.mark.parametrize("int_type", [i32, i64, u32, u64])
def test_var_declare_numpy(host_port, float_type, int_type):
    import sys
    with program() as prog:
        int_var = declare(int, value=int_type(1))
        int_arr = declare(int, value=np.array([1, 2, 3, 4, 5], dtype=int_type))
        bool_var = declare(bool, value=np.bool_(False))
        bool_arr = declare(bool, value=np.array([False, True, True, False, True],
                                                dtype=np.bool_))
        fixed_var = declare(fixed, value=float_type(0.5))
        fixed_arr = declare(fixed, value=np.arange(0, 1, 0.2, dtype=float_type))
        save(int_var, "a")
        save(bool_var, "b")
        save(fixed_var, "c")
        for i in range(5):
            save(int_arr[i], "int_arr")
            save(fixed_arr[i], "fixed_arr")
            save(bool_arr[i], "bool_arr")

    res = _run_sim(prog, host_port, ["a", "b", "c", "int_arr", "fixed_arr", "bool_arr"])
    assert 1 == res["a"][0]
    assert not res["b"][0]
    assert 0.5 == res["c"][0]
    assert np.array_equal(res["fixed_arr"], fixed_arange(0, 1, 0.2, float_type))
    assert np.array_equal(res["int_arr"], list(range(1, 6)))
    assert np.array_equal(res["bool_arr"], [False, True, True, False, True])


@pytest.mark.parametrize("float_type", [f16, f32, f64, f128])
@pytest.mark.parametrize("int_type", [i32, i64])
def test_var_assign_numpy(host_port, float_type, int_type):
    with program() as prog:
        a = declare(int)
        b = declare(bool)
        c = declare(fixed)
        assign(a, int_type(5))
        save(a, "a")
        assign(a, int_type(-9))
        save(a, "a")
        assign(b, np.bool_(True))
        save(b, "b")
        assign(c, float_type(0.85))
        save(c, "c")
        assign(c, float_type(-2.2))
        save(c, "c")

    res = _run_sim(prog, host_port, ["a", "b", "c"])
    assert np.array_equal(res["a"], [5, -9])
    assert res["b"][0]
    assert np.array_equal(res["c"], [float_to_fix(float_type(0.85)),
                                     float_to_fix(float_type(-2.2))])


@pytest.mark.parametrize("float_type", [f16, f32, f64, f128])
@pytest.mark.parametrize("int_type", [i32, i64, u32, u64])
def test_for_loop_numpy(host_port, float_type, int_type):
    with program() as prog:
        iter_f = declare(fixed, value=float_type(0))
        with for_(iter_f, init=int_type(0), cond=iter_f < float_type(5),
                  update=iter_f + float_type(0.5)):
            save(iter_f, "iter_f")
        iter_int = declare(int, value=int_type(0))
        with for_(iter_int, init=int_type(0), cond=iter_int < int_type(5),
                  update=iter_int + int_type(1)):
            save(iter_int, "iter_int")

    res = _run_sim(prog, host_port, ["iter_f", "iter_int"])
    assert np.array_equal(res["iter_f"], np.arange(0, 5, 0.5))
    assert np.array_equal(res["iter_int"], range(5))


@pytest.mark.parametrize("float_type", [f16, f32, f64, f128])
@pytest.mark.parametrize("int_type", [i32, i64, u32, u64])
def test_for_each_numpy(host_port, float_type, int_type):
    with program() as prog:
        iter_f = declare(fixed, value=float_type(0))
        with for_each_(iter_f, np.arange(0, 5, 0.5)):
            save(iter_f, "iter_f")
        iter_int = declare(int, value=int_type(0))
        with for_each_(iter_int, np.arange(0, 5, 1, dtype=i32)):
            save(iter_int, "iter_int")

    res = _run_sim(prog, host_port, ["iter_f", "iter_int"])
    assert np.array_equal(res["iter_f"], np.arange(0, 5, 0.5))
    assert np.array_equal(res["iter_int"], range(5))


@pytest.mark.parametrize("float_type", [f16, f32, f64, f128])
@pytest.mark.parametrize("int_type", [i32, i64, u32, u64])
def test_control_flow_numpy(host_port, float_type, int_type):
    with program() as prog:
        a = declare(int, value=int_type(10))
        b = declare(int, value=int_type(5))
        c = declare(fixed, value=float_type(2.2))
        d = declare(fixed, value=float_type(2.5))
        f = declare(bool, value=np.bool_(True))

        with if_(a < b):
            save(a, "a")
        with elif_(b < int_type(12)):
            save(b, "b")
        with else_():
            save(a, "a")

        with if_(d < c):
            save(c, "c")
        with elif_(d < float_type(2.51)):
            save(d, "d")

        with if_(f):
            save(f, "f")
        with else_():
            pass

    try:
        res = _run_sim(prog, host_port, ["a", "b", "c", "d", "f"])
    except Exception:
        raise ValueError(f"Wrong Branching")

    assert len(res["a"]) == 0
    assert len(res["c"]) == 0
    assert res["b"][0] == 5
    assert res["d"][0] == 2.5
    assert res["f"][0]


@pytest.mark.parametrize("float_type", [f16, f32, f64, f128])
@pytest.mark.parametrize("int_type", [i32, i64, u32, u64])
def test_while_loop_numpy(host_port, float_type, int_type):
    with program() as prog:
        iter_int = declare(int, value=i32(0))
        with while_(iter_int < i32(5)):
            save(iter_int, "iter_int")
            assign(iter_int, iter_int + i32(1))

        iter_float = declare(fixed, value=f32(0.0))
        with while_(iter_float < f32(1.0)):
            save(iter_float, "iter_float")
            assign(iter_float, iter_float + f32(0.2))

    res = _run_sim(prog, host_port, ["iter_int", "iter_float"])
    assert len(res["iter_int"]) > 0 and len(res["iter_float"]) > 0
    assert np.array_equal(res["iter_int"], range(5))
    ref_range = [(np.ceil(f32(0.2) * 2 ** 28) / 2 ** 28) * i for i in range(0, 5)]
    assert np.array_equal(res["iter_float"], ref_range)


@pytest.mark.parametrize("float_type", [f16, f32, f64, f128])
@pytest.mark.parametrize("int_type", [i32, i64, u32, u64])
def test_switch_case_numpy(host_port, float_type, int_type):
    with program() as p:
        y = declare(int, value=int_type(2))
        f = declare(fixed, value=float_type(0.5))

        with switch_(y):
            with case_(int_type(1)):
                save(False, "a")
            with case_(int_type(2)):
                save(True, "a")
            with default_():
                save(False, "a")

        assign(y, int_type(1))
        with switch_(y, unsafe=True):
            with case_(int_type(1)):
                save(True, "b")
            with case_(int_type(2)):
                save(False, "b")

        with switch_(f):
            with case_(float_type(0.2)):
                save(False, "c")
                save(True, "d")
            with case_(float_type(0.5)):
                save(True, "c")
                save(False, "d")

    res = _run_sim(p, host_port, ["a", "b", "c", 'd'])

    assert res["a"][0]
    assert res["b"][0]
    assert res["c"][0]
    assert not res["d"][0]


@pytest.mark.parametrize("float_type", [f16, f32, f64, f128])
def test_all_math_functions(host_port, float_type):
    '''Check all math functions under Math library with numpy inputs.
       Some of the functions are not supported in compiler, This test also checks that
        pure python behaviour is similar to numpy behaviour. (i.e, if tests fails on
        python input (literal or array), it is expected that it will fail on numpy as well.
    '''

    math_methods = [func for func in dir(Math) if callable(getattr(Math, func)) if not func.startswith("__")]
    math_methods_single_scalar = ["exp", "pow2", "ln", "log2", "log10", "sqrt", "inv_sqrt", "inv",
                      "elu", "aelu", "selu", "relu", "lrelu", "cos", "sin", "lrelu", "sin2pi", "cos2pi", "abs"]
    math_methods_two_scalars = ["pow", "div", "log", "plrelu"]
    math_methods_single_scalar_int_return = ["msb"]
    math_signle_array_methods = ["sum", "max", "min", "argmax", "argmin"]
    math_dual_array_methods = ["dot"]

    python_failed_tests = []
    for input_type in ("python", "numpy"):
        for method in math_methods: #math_methods:
            call_method = getattr(Math, method)
            return_value_type = int if method in math_methods_single_scalar_int_return + \
                                                  math_signle_array_methods + \
                                                  math_dual_array_methods else fixed
            options = 1
            literal_type = float_type if input_type == "numpy" else float
            array_type = np.array if input_type == "numpy" else list
            with program() as p:
                ret = declare(return_value_type, size=3)
                expected_ret = declare(return_value_type, size=3)
                if method in math_methods_single_scalar + math_methods_single_scalar_int_return:
                    expected_val = declare(fixed, value=0.5)
                    assign(ret[0], call_method(literal_type(0.5)))
                    assign(expected_ret[0], call_method(expected_val))
                elif method in math_methods_two_scalars:
                    assign(expected_ret[0], call_method(declare(fixed, value=1.5),
                                                        declare(fixed, value=2)))
                    x = declare(fixed, value=1.5)
                    assign(ret[0], call_method(x, literal_type(2)))
                    assign(x, 2)
                    assign(ret[1], call_method(literal_type(1.5), x))
                    assign(ret[2], call_method(literal_type(1.5), literal_type(2)))
                    options = 3
                elif method in math_signle_array_methods:
                    assign(ret[0], call_method(array_type([1,2,3])))
                    assign(expected_ret[0], call_method(declare(int, value=[1,2,3])))
                elif method in math_dual_array_methods:
                    x = declare(int, value=[3,2,1])
                    assign(ret[0], call_method(x,array_type([1,2,3])))
                    for i in range(3):
                        assign(x[i], i + 1)
                    assign(ret[1], call_method(array_type([3,2,1]), x))
                    assign(ret[2], call_method(array_type([3,2,1]), array_type([1,2,3])))
                    assign(expected_ret[0], call_method(declare(int, value=[3,2,1]), declare(int, value=[1,2,3])))
                    options = 3
                else:
                    raise ValueError(method)

                for i in range(3):
                    save(ret[i], f"ret{i}")
                save(expected_ret[0], "expected")

            logger.info(f"Checking: {method}")
            try:
                res = _run_sim(p, host_port, ["ret0", "ret1", "ret2", "expected"])
            except FailedToExecuteJobException as e:
                if input_type == "python":
                    python_failed_tests.append(method)
                else:
                    assert method in python_failed_tests
                continue

            assert all([res[f"ret{i}"][0] == res["expected"][0] for i in range(options)])


@pytest.mark.parametrize("float_type", [f16, f32, f64, f128])
@pytest.mark.parametrize("int_type", [i32, i64, u32, u64])
def test_casting(host_port, float_type, int_type):
    with program() as p:
        res_int = declare(int)
        res_fixed = declare(fixed)
        assign(res_int, Cast.mul_int_by_fixed(int_type(10), float_type(4)))
        save(res_int, "res_int")
        assign(res_fixed, Cast.mul_fixed_by_int(float_type(0.1), int_type(40)))
        save(res_fixed, "res_fixed")

    res = _run_sim(p, host_port, ["res_int", "res_fixed"])
    assert res["res_int"][0] == 40
    assert res["res_fixed"][0] == float_to_fix(float_type(0.1)) * 40


@pytest.mark.parametrize("int_type", [i32, i64, u32, u64])
def test_util(host_port, int_type):
    with program() as p:
        x = declare(int)
        assign(x, Util.cond(x >= int_type(0), int_type(1), int_type(0)))
        save(x, "x")
    res = _run_sim(p, host_port, ["x"])
    assert res["x"][0] == 1


@pytest.mark.parametrize("int_type", [i32, i64, u32, u64])
def test_random(host_port, int_type):
    with program() as p:
        x = declare(int)
        y = declare(int)
        rand = Random()
        rand.set_seed(int_type(12))
        assign(x, rand.rand_int(int_type(5)))
        rand.set_seed(12)
        assign(y, rand.rand_int(5))
        save(x, "x")
        save(y, "y")
    res = _run_sim(p, host_port, ["x", "y"])
    assert res["x"][0] == res["y"][0]


