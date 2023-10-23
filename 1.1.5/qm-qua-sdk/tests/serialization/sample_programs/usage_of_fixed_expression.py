import itertools

from qm.qua import *  # noqa

_fixed_expressions = [(lambda var: var)]
_fixed_usage_site = [
    ("play", lambda exp: play("pi", "q1")),
    ("frame_rotation_2pi", lambda exp: frame_rotation_2pi(exp, "q1")),
    ("update_frequency", lambda exp: update_frequency("q1", exp, "Hz", True)),
]

for exp_fn, (name, usage) in itertools.product(_fixed_expressions, _fixed_usage_site):
    with program() as prog:
        v = declare(fixed)
        exp = exp_fn(v)
        usage(exp)
    locals()[f"{exp}_{name}"] = prog
    del prog
