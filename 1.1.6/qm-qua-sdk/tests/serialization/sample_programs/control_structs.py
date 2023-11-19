from qm.qua import *
import numpy as np
i32 = np.int32
f32 = np.float32

with program() as for_each:
    x = declare(fixed)
    with for_each_(x, [0.1, 0.4, 0.6]):
        play("pulse" * amp(x), "element")
    with for_each_(x, [0.1, 0.4, 0.6]):
        play("pulse" * amp(x), "element")
    play("pulse" * amp(x), "element")


with program() as for_each_with_ts:
    x = declare(fixed)
    with for_each_(x, [0.1, 0.4, 0.6]):
        play("pulse" * amp(x), "element", timestamp_stream=str(x)+"ts")

with program() as numpy_for_each:
    x = declare(fixed, value=f32(0.5))
    with for_each_(x, np.array([0.1, 0.4, 0.6], dtype=f32)):
        play("pulse" * amp(x), "element")
    with for_each_(x, np.array([0, 1, 0.5], dtype=i32)):
        play("pulse" * amp(x), "element")
    play("pulse" * amp(x), "element")

with program() as for_each_2_dims:
    x = declare(fixed)
    y = declare(fixed)
    with for_each_((x, y), ([0.1, 0.4, 0.6], [0.3, -0.2, 0.1])):
        play("pulse1" * amp(x), "element")
        play("pulse2" * amp(y), "element")

with program() as for_each_numpy_2_dims:
    x = declare(fixed)
    y = declare(fixed)
    with for_each_((x, y), np.array(([0.1, 0.4, 0.6], [0.3, -0.2, 0.1]), dtype=f32)):
        play("pulse1" * amp(x), "element")
        play("pulse2" * amp(y), "element")

with program() as while_loop:
    y = declare(fixed)
    assign(y, 0)
    with while_(y <= 30):
        play("pulse", "element")
        assign(y, y + 1)

with program() as numpy_while_loop:
    y = declare(fixed)
    assign(y, 0.0)
    np_val_limit = i32(30)
    np_inc = i32(1)
    with while_(y <= np_val_limit):
        play("pulse", "element")
        assign(y, y + np_inc)

with program() as for_loop:
    y = declare(fixed)
    assign(y, 0)
    with for_(y, 0, y <= 30, y + 1):
        play("pulse", "element")
        assign(y, y + 1)

with program() as numpy_for_loop:
    y = declare(fixed)
    assign(y, i32(0))
    with for_(y, i32(0), y <= i32(30), y + i32(1)):
        play("pulse", "element")
        assign(y, y + i32(1))

with program() as infinite_loop:
    with infinite_loop_():
        play("pulse", "element")


with program() as condition:
    y = declare(fixed)

    with if_(y > 0):
        play("pulse", "element")

    with if_(y > 0):
        play("pulse", "element")
    with else_():
        play("other_pulse", "element")

    with if_(y > 0):
        play("pulse", "element")
    with elif_(y == 0):
        play("elif_pulse", "element")
    with else_():
        play("other_pulse", "element")


with program() as condition_with_numpy:
    y = declare(fixed)

    with if_(y > f32(0)):
        play("pulse", "element")

    with if_(y > f32(-1.2)):
        play("pulse", "element")
    with else_():
        play("other_pulse", "element")

    with if_(y > i32(0)):
        play("pulse", "element")
    with elif_(y == i32(0)):
        play("elif_pulse", "element")
    with else_():
        play("other_pulse", "element")


with program() as switch_case:
    y = declare(fixed)

    with switch_(y):
        with case_(1):
            play("op1", "qe")
        with case_(2):
            play("op2", "qe")
        with default_():
            play("default_op", "qe")

with program() as unsafe_switch_case:
    y = declare(fixed)

    with switch_(y, unsafe=True):
        with case_(1):
            play("op1", "qe")
        with case_(2):
            play("op2", "qe")
        with default_():
            play("default_op", "qe")


with program() as numpy_switch_case:
    x = declare(int, value=i32(3))
    y = declare(fixed, value=f32(0.5))

    with switch_(x):
        with case_(i32(1)):
            play("op1", "qe")
        with case_(i32(2)):
            play("op2", "qe")
        with default_():
            play("default_op", "qe")

    with switch_(y):
        with case_(f32(0.5)):
            play("op1", "qe")
        with case_(f32(1.0)):
            play("op2", "qe")
        with default_():
            play("default_op", "qe")

with program() as numpy_unsafe_switch_case:
    y = declare(fixed, value=i32(1))

    with switch_(y, unsafe=True):
        with case_(i32(1)):
            play("op1", "qe")
        with case_(i32(2)):
            play("op2", "qe")
        with default_():
            play("default_op", "qe")

with program() as check_pass:
    y = declare(int)
    with infinite_loop_():
        pass

    with for_each_(y, [1, 2]):
        pass

    with for_(y, 0, y < 1, y+0.5):
        pass

    with if_(y>1):
        pass
    with elif_(y>0):
        pass
    # with else_():
    #     pass

with program() as strict_timing:
    with strict_timing_():
        play("op1", "qe")
        play("op2", "qe")
