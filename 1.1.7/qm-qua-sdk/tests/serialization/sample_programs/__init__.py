from qm import _Program
from types import ModuleType

from tests.serialization.sample_programs import complex, control_structs, \
    input_stream, math, simple, streaming, usage_of_fixed_expression, var_declare, \
    var_ref


def to_dict(imp: ModuleType):
    prefix = imp.__name__.split(".")[-1]
    from qm import Program

    return {
        f"{prefix}.{k}": v for k, v in imp.__dict__.items() if isinstance(v, Program)
    }


all_programs = {}
for module in [simple, complex, var_declare, control_structs, streaming,
               usage_of_fixed_expression, var_ref, input_stream, math]:
    all_programs.update(to_dict(module))
