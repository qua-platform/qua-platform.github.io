import numpy as np
from qm.qua import *

i32 = np.int32
f32 = np.float32
with program() as util_cond:
    v = declare(int)
    a = declare(int)
    assign(v, Util.cond(a < 1, 0, 1))

with program() as numpy_util_cond:
    v = declare(int, value=i32(0))
    a = declare(int, value=i32(1))
    assign(v, Util.cond(a < i32(1), i32(0), i32(1)))

with program() as random_rand_int:
    v = declare(int)
    assign(v, Random().rand_int(v))

with program() as random_rand_int_numpy:
    v = declare(int)
    assign(v, Random().rand_int(i32(5)))
    assign(v, Random().rand_int(f32(4.2)))
    assign(v, Random().rand_int(np.bool_(True)))

with program() as random_rand_fixed:
    v = declare(int)
    assign(v, Random().rand_fixed())

with program() as cast_unsafe_cast_fixed:
    v = declare(int, value=1)
    assign(v, Cast.unsafe_cast_fixed(v))

with program() as cast_unsafe_cast_bool:
    v = declare(int, value=1)
    assign(v, Cast.unsafe_cast_bool(v))

with program() as cast_unsafe_cast_int:
    v = declare(int, value=1)
    assign(v, Cast.unsafe_cast_int(v))

with program() as cast_unsafe_numpy:
    a = declare(int, value=1)
    b = declare(fixed, value=1)
    c = declare(bool, value=1)
    assign(a, Cast.unsafe_cast_int(f32(2)))
    assign(b, Cast.unsafe_cast_fixed(i32(3)))
    assign(c, Cast.unsafe_cast_bool(i32(1)))

with program() as cast_cast_int:
    v = declare(float, value=1.5)
    assign(v, Cast.to_int(v))

with program() as cast_cast_int_numpy:
    v = declare(float, value=1.5)
    assign(v, Cast.to_int(f32(2)))

with program() as cast_cast_bool:
    v = declare(float, value=1.5)
    assign(v, Cast.to_bool(v))

with program() as cast_cast_bool_numpy:
    v = declare(float, value=1.5)
    assign(v, Cast.to_bool(i32(1)))

with program() as cast_cast_fixed:
    v = declare(float, value=1.5)
    assign(v, Cast.to_fixed(v))

with program() as cast_cast_fixed_numpy:
    v = declare(float, value=1.5)
    assign(v, Cast.to_fixed(i32(2)))

with program() as cast_mul_fixed_by_int:
    v = declare(float, value=1.5)
    i = declare(int, value=1)
    assign(v, Cast.mul_fixed_by_int(v, i))

with program() as cast_mul_fixed_by_int_numpy:
    v = declare(float, value=1.5)
    i = declare(int, value=1)
    assign(v, Cast.mul_fixed_by_int(v, f32(2)))
    assign(v, Cast.mul_fixed_by_int(i32(2), i))

with program() as cast_mul_int_by_fixed:
    v = declare(float, value=1.5)
    i = declare(int, value=1)
    assign(v, Cast.mul_int_by_fixed(i, v))

with program() as cast_mul_int_by_fixed_numpy:
    v = declare(float, value=1.5)
    i = declare(int, value=1)
    assign(v, Cast.mul_int_by_fixed(f32(2), v))
    assign(v, Cast.mul_int_by_fixed(i, i32(1)))

with program() as math_log:
    x = declare(fixed, value=1)
    y = declare(fixed, value=2)
    v = declare(float, value=1.5)
    assign(v, Math.log(x, y))

with program() as math_log_with_numpy:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.log(x, i32(2)))
    assign(v, Math.log(f32(2), x))

with program() as math_pow:
    x = declare(fixed, value=1)
    y = declare(fixed, value=2)
    v = declare(float, value=1.5)
    assign(v, Math.pow(x, y))

with program() as math_pow_with_numpy:
    x = declare(fixed, value=2)
    y = declare(fixed, value=2)
    v = declare(float, value=1.5)
    assign(v, Math.pow(x, i32(2)))
    assign(v, Math.pow(f32(2), y))

with program() as math_div:
    x = declare(fixed, value=1)
    y = declare(fixed, value=2)
    v = declare(float, value=1.5)
    assign(v, Math.div(x, y))

with program() as math_div_with_numpy:
    x = declare(fixed, value=1)
    y = declare(fixed, value=2)
    v = declare(float, value=1.5)
    assign(v, Math.div(x, i32(2)))
    assign(v, Math.div(f32(3), y))

with program() as math_exp:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.exp(x))

with program() as math_pow2:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.pow2(x))

with program() as math_ln:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.ln(x))

with program() as math_log2:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.log2(x))

with program() as math_log10:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.log10(x))

with program() as math_sqrt:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.sqrt(x))

with program() as math_inv_sqrt:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.inv_sqrt(x))

with program() as math_inv:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.inv(x))

with program() as math_msb:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.msb(x))

with program() as math_elu:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.elu(x))

with program() as math_aelu:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.aelu(x))

with program() as math_selu:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.selu(x))

with program() as math_relu:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.relu(x))

with program() as math_plrelu:
    x = declare(fixed, size=2)
    y = declare(fixed, size=2)
    v = declare(float, value=1.5)
    assign(v, Math.plrelu(x, y))

with program() as math_plrelu_with_numpy:
    x = declare(fixed, size=2)
    y = declare(fixed, size=2)
    v = declare(float, value=1.5)
    assign(v, Math.plrelu(x, f32(2)))
    assign(v, Math.plrelu(f32(2), y))

with program() as math_lrelu:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.lrelu(x))

with program() as math_sin2pi:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.sin2pi(x))

with program() as math_cos2pi:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.cos2pi(x))

with program() as math_abs:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.abs(x))

with program() as math_sin:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.sin(x))

with program() as math_cos:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.cos(x))

with program() as math_sum:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.sum(x))

with program() as math_max:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.max(x))

with program() as math_min:
    x = declare(fixed, value=1)
    v = declare(float, value=1.5)
    assign(v, Math.min(x))

with program() as math_argmax:
    x = declare(fixed, value=[1, 2])
    v = declare(float, value=1.5)
    assign(v, Math.argmax(x))

with program() as math_argmin:
    x = declare(fixed, value=[1, 2])
    v = declare(float, value=1.5)
    assign(v, Math.argmin(x))

with program() as dot:
    x = declare(fixed, size=2)
    y = declare(fixed, size=2)
    v = declare(float, value=1.5)
    assign(v, Math.dot(x, y))

with program() as expressions:
    x = declare(int)
    y = declare(int)
    z = declare(int)
    f = declare(fixed)
    assign(z, (x * y + z) * z)
    assign(f, Math.div((x + y) * z, z - 2))

with program() as test_single_math_operations_with_python_literals:
    x = declare(fixed)
    for operation in ["exp", "pow2", "ln", "log2", "log10", "sqrt", "inv_sqrt", "inv",
                      "msb", "elu", "aelu", "selu", "relu", "lrelu", "sin2pi", "cos2pi",
                      "abs", "sin", "cos"]:
        assign(x, getattr(Math, operation)(0.5))

with program() as test_single_math_operations_with_numpy_literals:
    x = declare(fixed)
    for operation in ["exp", "pow2", "ln", "log2", "log10", "sqrt", "inv_sqrt", "inv",
                      "msb", "elu", "aelu", "selu", "relu", "lrelu", "sin2pi", "cos2pi",
                      "abs", "sin", "cos"]:
        assign(x, getattr(Math, operation)(f32(0.5)))

with program() as test_vector_operation_with_python_array:
    x = declare(int)
    for operation in ["sum", "max", "min", "argmax", "argmin"]:
        assign(x, getattr(Math, operation)([-1.1, 1.2, 2.3, 3.4, 4.5]))
        assign(x, getattr(Math, operation)([-1, 1, 2, 3, 4]))

    arr = declare(int, value=[0, 1, 2, 3])
    assign(x, Math.dot(arr, [1, 2, 3, 4]))
    assign(x, Math.dot([1, 2, 3, 4], arr))
    assign(x, Math.dot([1, 2, 3, 4], [0, 1, 2, 3]))

with program() as test_vector_operation_with_numpy_array:
    x = declare(int)
    for operation in ["sum", "max", "min", "argmax", "argmin"]:
        assign(x, getattr(Math, operation)(np.array([-1.1, 1.2, 2.3, 3.4, 4.5], dtype=f32)))
        assign(x, getattr(Math, operation)(np.array([-1, 1, 2, 3, 4], dtype=i32)))

    arr = declare(int, value=np.array([0, 1, 2, 3]))
    assign(x, Math.dot(arr, np.array([1, 2, 3, 4])))
    assign(x, Math.dot(np.array([1, 2, 3, 4]), arr))

with program() as expressions_with_numpy:
    x = declare(int)
    y = declare(int)
    z = declare(int)
    f = declare(fixed)
    assign(z, (x * f32(0.2) + z) * f32(1.2))
    assign(f, Math.div((x + f32(1.1)) * z, z - f32(1)))
