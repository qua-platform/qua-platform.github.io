from qm.qua import *

f32 = np.float32
i32 = np.int32

with program() as just_play:
    play("pulse", "element")

with program() as play_with_timestamp:
    play("pulse", "element", timestamp_stream="ts")

with program() as play_amp:
    x = declare(int)
    play(
        "pulse" * amp(x),
        "element",
    )

with program() as play_numpy_amp:
    play(
        "pulse" * amp(f32(0.5), f32(0.2),
                      f32(0.7), f32(0.4)),
        "element",
    )

with program() as play_various:
    x = declare(fixed)
    x2 = declare(fixed)
    x3 = declare(fixed)
    x4 = declare(fixed)
    play(
        "pulse" * amp(1.5),
        "element",
    )
    play(
        "pulse" * amp(2.5),
        "element",
    )
    play(
        "pulse" * amp(8.5),
        "element",
    )
    play(
        "pulse" * amp(8.5),
        "element",
    )
    play(
        "pulse" * amp(0.9, 0.1, 0.2, 0.3),
        "element",
    )
    play("pulse" * amp(x, x2, x3, x4), "element")
    play("pulse" * amp(x), "element", duration=5)
    play("pulse" * amp(x), "element", condition=x > 0)
    play("pulse" * amp(x), "element", chirp=(-25000, "Hz/nsec"), continue_chirp=True)
    play(
        "pulse" * amp(x),
        "element",
        chirp=([199, 550, -997, 1396], [0, 15196, 25397, 56925], "Hz/nsec"),
    )
    play("pulse" * amp(x), "element", truncate=10)
    play("pulse" * amp(x), "element", target="row")
    play(ramp(x), "element", duration=5)

with program() as play_various_with_numpy:
    x = declare(fixed, value=f32(0.0))
    x2 = declare(fixed, value=f32(0.1))
    x3 = declare(fixed, value=f32(0.0))
    x4 = declare(fixed, value=f32(0.0))
    play(
        "pulse" * amp(f32(1.5)),
        "element",
    )
    play(
        "pulse" * amp(f32(2.5)),
        "element",
    )
    play(
        "pulse" * amp(f32(8.5)),
        "element",
    )
    play(
        "pulse" * amp(f32(8.5)),
        "element",
    )
    play(
        "pulse" * amp(*np.array([0.9, 0.1, 0.2, 0.3], dtype=f32)),
        "element",
    )
    play("pulse" * amp(x, x2, x3, x4), "element")
    play("pulse" * amp(x), "element", duration=i32(5))
    play("pulse" * amp(x), "element", condition=x > f32(0))
    play("pulse" * amp(x), "element", chirp=(i32(-25000), "Hz/nsec"), continue_chirp=True)
    play(
        "pulse" * amp(x),
        "element",
        chirp=(np.array([199, 550, -997, 1396], dtype=i32),
               np.array([0, 15196, 25397, 56925], dtype=i32), "Hz/nsec"),
    )
    play("pulse" * amp(x), "element", truncate=i32(10))
    play("pulse" * amp(x), "element", target="row")
    play(ramp(x), "element", duration=i32(5))

with program() as for_each:
    x = declare(int)
    with for_each_(x, [0.1, 0.4, 0.6]):
        play("pulse", "element")

with program() as set_dc_offset_prog:
    set_dc_offset("q1", "pi", 0.5)
