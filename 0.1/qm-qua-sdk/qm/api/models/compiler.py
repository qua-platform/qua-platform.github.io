from typing import List, Optional
from dataclasses import field, dataclass

from qm.grpc.qua import QuaProgramCompilerOptions


@dataclass
class CompilerOptionArguments:
    strict: Optional[bool] = field(default=None)

    flags: List[str] = field(default_factory=list)


def _get_request_compiler_options(
    compiler_options: CompilerOptionArguments,
) -> QuaProgramCompilerOptions:
    flags = compiler_options.flags
    if compiler_options.strict:
        flags.append("strict")

    return QuaProgramCompilerOptions(flags=compiler_options.flags)
