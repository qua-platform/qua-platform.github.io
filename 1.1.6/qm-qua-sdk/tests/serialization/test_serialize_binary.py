import pytest

from qm import Program
from qm.grpc.qua_config import QuaConfig
from qm.program import load_config
from tests.serialization.sample_config import config
from tests.serialization.sample_programs.complex import prog, measure_amp, measure_demod


@pytest.mark.parametrize("program", [prog, measure_amp, measure_demod])
def test_to_binary(program: Program):
    binary = program.to_protobuf(config)
    assert isinstance(binary, bytes)
    assert len(binary) > 0

    new_program = Program.from_protobuf(binary)
    assert new_program._program.config == load_config(config)

    new_program._program.config = QuaConfig()  # The original program had no config
    assert new_program._program == program._program


@pytest.mark.parametrize("program", [prog, measure_amp, measure_demod])
def test_to_file(program: Program, tmp_path):
    path = tmp_path / "program.bin"
    program.to_file(path, config)

    assert path.exists()
    assert path.stat().st_size > 0

    new_program = Program.from_file(path)
    new_program._program.config = QuaConfig()
    assert new_program._program == program._program
