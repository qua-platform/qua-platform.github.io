# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: qm/pb/compiler.proto
# plugin: python-betterproto
from dataclasses import dataclass
from typing import (
    Dict,
    List,
)

import betterproto
import betterproto.lib.google.protobuf as betterproto_lib_google_protobuf

from .. import (
    general_messages as _general_messages__,
    qm_manager as _qm_manager__,
    qua as _qua__,
)


@dataclass(eq=False, repr=False)
class QuaValues(betterproto.Message):
    int_value: int = betterproto.uint32_field(1)
    double_value: float = betterproto.double_field(2)
    boolean_value: bool = betterproto.bool_field(3)


@dataclass(eq=False, repr=False)
class CompileRequest(betterproto.Message):
    """The request message containing the user's name."""

    program: "_qua__.QuaProgram" = betterproto.message_field(1)
    job_id: str = betterproto.string_field(2)
    """used for logging inside internal services"""


@dataclass(eq=False, repr=False)
class CompileResponse(betterproto.Message):
    ok: bool = betterproto.bool_field(1)
    messages: List["CompilerMessage"] = betterproto.message_field(2)
    binary: bytes = betterproto.bytes_field(3)
    metadata: str = betterproto.string_field(4)
    debug: Dict[str, str] = betterproto.map_field(
        30, betterproto.TYPE_STRING, betterproto.TYPE_STRING
    )


@dataclass(eq=False, repr=False)
class CompilerMessage(betterproto.Message):
    message: str = betterproto.string_field(1)
    level: "_general_messages__.MessageLevel" = betterproto.enum_field(2)


@dataclass(eq=False, repr=False)
class ValidationResponse(betterproto.Message):
    messages: List["_qm_manager__.ConfigValidationMessage"] = betterproto.message_field(
        1
    )


@dataclass(eq=False, repr=False)
class DynamicConfig(betterproto.Message):
    """
    A config that is similar to JSON in structure and can be converted to the
    real configIt has support for versioning
    """

    version: int = betterproto.uint32_field(1)
    root: "betterproto_lib_google_protobuf.Struct" = betterproto.message_field(2)