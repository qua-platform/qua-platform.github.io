from types import ModuleType

from tests.serialization.sample_programs import complex
from tests.serialization.sample_programs import control_structs
from tests.serialization.sample_programs import simple
from tests.serialization.sample_programs import streaming
from tests.serialization.sample_programs import var_declare
from tests.serialization.sample_programs import usage_of_fixed_expression
from tests.serialization.sample_programs import var_ref
from tests.serialization.sample_programs import input_stream
from tests.serialization.sample_programs import math


def to_dict(imp: ModuleType):
    prefix = imp.__name__.split(".")[-1]
    from qm import Program

    return {
        f"{prefix}.{k}": v for k, v in imp.__dict__.items() if isinstance(v, Program)
    }


all_programs = {}
all_programs.update(to_dict(simple))
all_programs.update(to_dict(complex))
all_programs.update(to_dict(var_declare))
all_programs.update(to_dict(control_structs))
all_programs.update(to_dict(streaming))
all_programs.update(to_dict(usage_of_fixed_expression))
all_programs.update(to_dict(var_ref))
all_programs.update(to_dict(input_stream))
all_programs.update(to_dict(math))
