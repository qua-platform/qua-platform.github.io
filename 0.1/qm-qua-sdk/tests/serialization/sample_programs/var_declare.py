import numpy as np

from qm.qua import *

i32 = np.int32
f32 = np.float32

with program() as just_declare:
    x = declare(int)

with program() as simple_declare:
    declare(int)
    declare(bool)
    declare(fixed)
    declare(float)

with program() as var_declare_with_size:
    for i in range(1, 5):
        declare(int, size=i)
        declare(bool, size=i)
        declare(fixed, size=i)
        declare(float, size=i)

with program() as var_declare_with_numpy_size:
    declare(int, size=i32(i))
    declare(bool, size=i32(i))
    declare(fixed, size=i32(i))
    declare(float, size=i32(i))

with program() as scalar_declare_with_init:
    for i in range(5):
        declare(int, value=i)
        declare(bool, value=i % 2)
        declare(fixed, value=i)
        declare(float, value=i)

with program() as scalar_declare_with_numpy_init:
    for i in np.arange(5):
        declare(int, value=i)
        declare(bool, value=i % 2)
        declare(fixed, value=i / 6)
        declare(float, value=i / 6)

with program() as array_declare_with_init:
    for i in range(5):
        declare(int, value=[i * j for j in range(5)])
        declare(bool, value=[(i * j) % 2 for j in range(5)])
        declare(fixed, value=[i * j for j in range(5)])
        declare(float, value=[i * j for j in range(5)])

with program() as array_declare_with_numpy_init:
    for i in range(5):
        declare(int, value=np.random.randint(low=-2 ** 31 + 1, high=2 ** 31 - 1,
                                             dtype=i32))
        declare(bool, value=[np.bool_((i * j) % 2) for j in range(5)])
        _arr_val = np.random.uniform(-8, 8 - (2 ** -16), 5)
        declare(fixed, value=_arr_val)
        declare(float, value=_arr_val)

with program() as test:
    # with init value
    for i in range(5):
        declare(int, value=[i * j for j in range(5)])
        declare(bool, value=[(i * j) % 2 for j in range(5)])
        declare(fixed, value=[i * j for j in range(5)])
        declare(float, value=[i * j for j in range(5)])

with program() as declare_bug:
    v1 = declare(int, value=50)
    v2 = declare(int, value=50)
    v3 = declare(int, value=50)
    v4 = declare(fixed, value=1.0)
    with infinite_loop_():
        update_frequency("resonator_3616", 200000000, "Hz", False)
        update_frequency("qubit1_8482", 200000000, "Hz", False)
        assign(v1, 50)
        assign(v2, 50)
        assign(v3, 50)
        play("qubit1-cal" * amp(v4), "qubit1_8482", duration=v1)
        wait(v1, "qubit1_8482")
        play("qubit1-cal" * amp(v4), "qubit1_8482", duration=v1)
        play("qubit1-cal" * amp(0.25), "qubit1_8482")
        play("qubit1-cal" * amp(v4), "qubit1_8482", duration=v1)
        align("resonator_3616", "qubit1_8482")
        wait(3000, "qubit1_8482")
        play("res-readout", "resonator_3616", duration=1000)
