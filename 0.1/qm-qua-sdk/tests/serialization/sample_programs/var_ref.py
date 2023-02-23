from qm.qua import *
import numpy as np

with program() as just_ref:
    x = declare(int)
    save(x, "x")

with program() as with_size:
    a0 = declare(int)
    b0 = declare(bool)
    c0 = declare(fixed)
    d0 = declare(float)

    a1 = declare(int, size=1)
    b1 = declare(bool, size=1)
    c1 = declare(fixed, size=1)
    d1 = declare(float, size=1)

    assign(a0, a1[0])
    assign(b0, b1[0])
    assign(c0, c1[0])
    assign(d0, d1[0])


with program() as array_ref_and_length:
    a0 = declare(int, size=10)
    v0 = declare(int)
    assign(v0, a0.length())
    assign(a0[v0-1], v0)


with program() as assign_with_numpy_vals:
    a0 = declare(int)
    b0 = declare(bool)
    c0 = declare(fixed)
    d0 = declare(float)

    a1 = np.int32(2)
    b1 = np.bool_(False)
    c1 = np.float32(0.5)
    d1 = np.float32(0.25)

    assign(a0, a1)
    assign(b0, b1)
    assign(c0, c1)
    assign(d0, d1)

with program() as io_values:
    a0 = declare(int)
    assign(a0, IO1)
