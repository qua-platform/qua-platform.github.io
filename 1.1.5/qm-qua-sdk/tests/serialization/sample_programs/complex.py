from qm.qua import *  # noqa
import numpy as np

i32 = np.int32
f32 = np.float32

with program() as prog:
    x = declare(int)
    play("pi", "q1", timestamp_stream="timestamp_stream1")
    # literal duration
    play("pi", "q1", duration=5, timestamp_stream="label1")
    stream = declare_stream()
    play("pi", "q1", duration=5, timestamp_stream=stream)
    with stream_processing():
        stream.save_all("label2")
    # variable duration
    play("pi", "q1", duration=x)
    assign(x, 1)
    assign(x, x + 1)
    measure("pi", "q1")
    measure("pi" * amp(x), "q1", timestamp_stream="label3")
    wait(10, "q1")
    wait(10, "q1", "q2")
    wait(x, "q1")
    pause()
    update_frequency("q1", 1, "Hz", True)
    fast_frame_rotation(0.5, -0.5, "q1")
    update_correction("q1", 1.0, 0.5, 0.5, 1.0)
    align("q1", "q2")
    reset_phase("q1")
    ramp_to_zero("q1")
    ramp_to_zero("q1", 20)
    wait_for_trigger("q1")
    wait_for_trigger("q1", "pi")
    frame_rotation(1.0, "q1")
    frame_rotation(1, "q1")
    frame_rotation(1, "q1", "q2")
    frame_rotation_2pi(1.0, "q1")
    frame_rotation_2pi(1, "q1")
    frame_rotation_2pi(1.0, "q1", "q2")
    reset_frame("q1")
    reset_frame("q1", "q2")


with program() as various_statements_with_numpy:
    x = declare(int, value=i32(0))
    play("pi", "q1")
    # literal duration
    play("pi", "q1", duration=i32(5))
    # variable duration
    play("pi", "q1", duration=x)
    assign(x, i32(1))
    assign(x, x + i32(1))
    measure("pi", "q1")
    measure("pi" * amp(x), "q1")
    wait(2, "q1")
    wait(i32(10), "q1")
    wait(i32(10), "q1", "q2")
    wait(x, "q1")
    update_frequency("q1", i32(1), "Hz", True)
    update_correction("q1", *np.array([1.0, 0.5, 0.5, 1.0], dtype=f32))
    ramp_to_zero("q1", i32(20))
    frame_rotation(f32(1.0), "q1")
    frame_rotation(i32(1), "q1")
    frame_rotation(i32(1), "q1", "q2")
    frame_rotation_2pi(f32(1.0), "q1")
    frame_rotation_2pi(i32(1), "q1")
    frame_rotation_2pi(f32(1.0), "q1", "q2")
    set_dc_offset("q1", "1", f32(0.7))


with program() as measure_demod:
    I = declare(fixed)
    Q = declare(fixed)
    measure("demod", "element", None, ("cos_weights", I), ("sin_weights", Q), timestamp_stream=None)

with program() as measure_processes:
    I = declare(fixed)
    measure("demod", "element", None, ("optimized_weights", "out1", I), timestamp_stream=None)

with program() as measure_processes_integration:
    A = declare(fixed, size=4)
    D = declare(fixed)
    measure("demod", "element", None, integration.full("integW1", D, "out1"), timestamp_stream="label1")
    measure(
        "demod", "element", None, integration.moving_window("integW1", A, 7, 7, "out1")
    )
    measure("demod", "element", None, integration.accumulated("integW1", A, 7, "out1"))

with program() as measure_processes_demod:
    A = declare(fixed, size=10)
    B = declare(fixed, size=4)
    C = declare(fixed, size=4)
    D = declare(fixed, size=4)
    E = declare(fixed)
    measure("demod", "element", None, demod.full("cos", E, "out1"))
    measure("demod", "element", None, demod.sliced("cos", A, 7, "out1"))
    measure("demod", "element", None, demod.accumulated("integW1", B, 7, "out1"))
    measure("demod", "element", None, demod.moving_window("integW1", C, 7, 3, "out1"))

with program() as measure_processes_dualdemod:
    A = declare(fixed, size=10)
    B = declare(fixed, size=4)
    C = declare(fixed, size=4)
    D = declare(fixed, size=4)
    E = declare(fixed)
    measure("demod", "element", None, dual_demod.full("cos", "out1", "cos", "out1", E))
    measure(
        "demod", "element", None, dual_demod.sliced("cos", "out1", "cos", "out1", 7, A)
    )
    measure(
        "demod",
        "element",
        None,
        dual_demod.accumulated("cos", "out1", "cos", "out1", 7, A),
    )
    measure(
        "demod",
        "element",
        None,
        dual_demod.moving_window("cos", "out1", "cos", "out1", 7, 3, C),
    )

with program() as measure_processes_dualintegration:
    A = declare(fixed, size=10)
    B = declare(fixed, size=4)
    C = declare(fixed, size=4)
    D = declare(fixed, size=4)
    E = declare(fixed)
    measure(
        "demod", "element", None, dual_integration.full("cos", "out1", "cos", "out1", E)
    )
    measure(
        "demod",
        "element",
        None,
        dual_integration.sliced("cos", "out1", "cos", "out1", 7, A),
    )
    measure(
        "demod",
        "element",
        None,
        dual_integration.accumulated("cos", "out1", "cos", "out1", 7, A),
    )
    measure(
        "demod",
        "element",
        None,
        dual_integration.moving_window("cos", "out1", "cos", "out1", 7, 3, C),
    )

with program() as time_tagging_prog:
    result1 = declare(int, size=10)
    counts1 = declare(int, value=0)
    measure("demod", "element", None, time_tagging.analog(result1, 50, counts1, "out1"))
    measure("demod", "element", None, time_tagging.analog(result1, 50, counts1))
    measure("demod", "element", None, time_tagging.high_res(result1, 50, counts1, "out1"))
    measure("demod", "element", None, time_tagging.high_res(result1, 50, counts1))
    result2 = declare(int, size=2)
    counts2 = declare(int, value=0)
    measure("demod", "element", None, time_tagging.analog(result2, 100 * 4, counts2, "out2"))
    measure("demod", "element", None, time_tagging.analog(result2, 100 * 4, counts2))

with program() as opd_prog:
    result1 = declare(int, size=10)
    counts1 = declare(int, value=0)
    time_tag_result = declare(int)
    measure("demod", "element", None, time_tagging.digital(result1, 50, counts1, "out1"))
    measure("demod", "element", None, time_tagging.digital(result1, 50, counts1))
    result2 = declare(int, size=2)
    counts2 = declare(int, value=0)
    measure("demod", "element", None, counting.digital(counts2, 100 * 4, "opd2"))
    measure("demod", "element", None, counting.digital(counts2, 100 * 4))
    wait_for_trigger('element', trigger_element='opd1')
    wait_for_trigger('element', pulse_to_play='bla', trigger_element='opd1')
    wait_for_trigger('element', trigger_element=('el2', 'opd1'))
    wait_for_trigger('element', trigger_element=('el2', 'opd1'), time_tag_target=time_tag_result)

with program() as counting_prog:
    result1 = declare(int)
    measure("demod", "element", None, counting.digital(result1, 10, "out1"))

with program() as measure_amp:
    I = declare(fixed)
    Q = declare(fixed)
    x = declare(int)
    measure("demod" * amp(x), "element", None, ("cos_weights", I), ("sin_weights", Q))
    measure(
        "demod" * amp(1, 2, 3, 4),
        "element",
        None,
        ("cos_weights", I),
        ("sin_weights", Q),
    )
