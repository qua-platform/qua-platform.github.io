import betterproto
import types

import pytest

from qm.grpc.qua import QuaProgram
from qm.serialization.qua_serializing_visitor import QuaSerializingVisitor
from qm.exceptions import QmQuaException
from qm.grpc.qua_config import QuaConfig
from .sample_programs import all_programs
from qm.serialization.generate_qua_script import StripLocationVisitor, generate_qua_script, RenameStreamVisitor
from qm.qua import switch_, case_, default_, if_, else_, elif_
from qm.qua import program, declare, play
from .sample_programs.control_structs import for_each_with_ts
from .sample_programs.simple import play_with_timestamp, just_play, program_with_fast_frame_rotation

program_names = list(all_programs.keys())


def standardize_program_for_comparison(prog: QuaProgram) -> QuaProgram:
    """There are things in the PB model that if they are different, the programs behaves exactly the same.
    These 3 things are
    1. the value of the loc field, that tells where the command was defined
    2. the names of the variables, as long as the commands are the same.
    3. the order of the variables in the result analysis
    """
    StripLocationVisitor.strip(prog)
    RenameStreamVisitor().visit(prog)
    prog.result_analysis.model = sorted(prog.result_analysis.model, key=str)
    return prog


def assert_programs_are_equal(prog1: QuaProgram, prog2: QuaProgram) -> None:
    prog1 = standardize_program_for_comparison(prog1)
    prog2 = standardize_program_for_comparison(prog2)
    assert prog1 == prog2


@pytest.mark.parametrize("name", program_names)
def test_all_programs(name):
    config = QuaConfig()
    prog = all_programs[name].build(config)

    visitor = QuaSerializingVisitor()
    visitor.visit(betterproto.deepcopy(prog))

    generated_mod = types.ModuleType("gen")
    new_var = visitor.out()
    print("")
    print("parsed program:")
    print(new_var)
    exec(new_var, generated_mod.__dict__)

    gen_prog = generated_mod.prog.build(config)
    assert_programs_are_equal(prog, gen_prog)


def test_programs_with_timestamp():
    assert play_with_timestamp.metadata.uses_command_timestamps
    assert for_each_with_ts.metadata.uses_command_timestamps


def test_program_with_fast_frame_rotation():
    assert program_with_fast_frame_rotation.metadata.uses_fast_frame_rotation


def test_program_without_timestamp():
    assert not just_play.metadata.uses_command_timestamps
    assert not just_play.metadata.uses_fast_frame_rotation


@pytest.mark.parametrize("name", program_names)
def test_all_programs_with_function(name):
    result = generate_qua_script(all_programs[name], None)
    assert "SERIALIZATION WAS NOT COMPLETE" not in result
    assert "SERIALIZATION VALIDATION ERROR" not in result


def test_trying_to_generate_in_scope():
    with program() as prog:
        x = declare(int)
        play(
            "pulse",
            "element",
        )
        with pytest.raises(RuntimeError):
            result = generate_qua_script(prog, None)


def find_prog(mod):
    for value in mod.__dict__.values():
        if type(value).__name__ == "_Program":
            return value


def program_string(prog: betterproto.Message) -> str:
    """Will create a canonized string representation of the program
    warning: Will modify the passed in program
    """
    StripLocationVisitor.strip(prog)
    return prog.to_json(2)


def test_dual_default_statements():
    with pytest.raises(QmQuaException):
        with program():
            x = declare(int)
            with switch_(x):
                with case_(1):
                    play("first_pulse", "element")
                with default_():
                    play("other_pulse", "element")
                with default_():
                    play("other_pulse", "element")


def test_else_placement():
    with pytest.raises(QmQuaException):
        with program():
            x = declare(int)
            with if_(x > 2):
                play("pulse", "element")
            with else_():
                play("third_pulse", "element")
            with elif_(x > -2):
                play("other_pulse", "element")

    with pytest.raises(QmQuaException):
        with program():
            x = declare(int)
            with if_(x > 2):
                play("pulse", "element")
            with else_():
                play("third_pulse", "element")
            with else_():
                play("third_pulse", "element")
