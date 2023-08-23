import warnings

from qm.program.program import Program

_Program = Program

warnings.warn(
    "'qm.program._Program' is moved as of 1.1.0 and will be removed in 1.2.0. " "use 'qm.Program' instead",
    category=DeprecationWarning,
)
