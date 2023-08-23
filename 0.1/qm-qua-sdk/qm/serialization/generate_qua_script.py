import re
import sys
import types
import datetime
import traceback
from typing import Any, Dict, Optional

import betterproto
import numpy as np

from qm import Program, version
from qm.program import load_config
from qm.grpc.qua_config import QuaConfig
from qm.exceptions import ConfigSerializationException
from qm.program.ConfigBuilder import convert_msg_to_config
from qm.serialization.qua_node_visitor import QuaNodeVisitor
from qm.serialization.qua_serializing_visitor import QuaSerializingVisitor

SERIALIZATION_VALIDATION_ERROR = "SERIALIZATION VALIDATION ERROR"

LOADED_CONFIG_ERROR = "LOADED CONFIG SERIALIZATION ERROR"

CONFIG_ERROR = "CONFIG SERIALIZATION ERROR"

SERIALIZATION_NOT_COMPLETE = "SERIALIZATION WAS NOT COMPLETE"


def generate_qua_script(prog: Program, config: Optional[dict] = None) -> str:
    if prog.is_in_scope():
        raise RuntimeError("Can not generate script inside the qua program scope")

    proto_config = None
    if config is not None:
        try:
            proto_config = load_config(config)
        except Exception as e:
            raise RuntimeError(
                "Can not generate script - bad config",
            ) from e

    proto_prog = prog.build(QuaConfig())
    return _generate_qua_script_pb(proto_prog, proto_config, config)


def _generate_qua_script_pb(proto_prog, proto_config: Optional, original_config: Optional):
    extra_info = ""
    serialized_program = ""
    pretty_original_config = None

    if original_config is not None:
        try:
            pretty_original_config = _print_config(original_config)
        except Exception as e:
            trace = traceback.format_exception(*sys.exc_info())
            extra_info = extra_info + _error_string(e, trace, CONFIG_ERROR)
            pretty_original_config = original_config

    pretty_proto_config = None
    if proto_config is not None:
        try:
            normalized_config = convert_msg_to_config(proto_config)
            pretty_proto_config = _print_config(normalized_config)
        except Exception as e:
            trace = traceback.format_exception(*sys.exc_info())
            extra_info = extra_info + _error_string(e, trace, LOADED_CONFIG_ERROR)

    try:
        visitor = QuaSerializingVisitor()
        visitor.visit(proto_prog)
        serialized_program = visitor.out()

        extra_info = extra_info + _validate_program(proto_prog, serialized_program)
    except Exception as e:
        trace = traceback.format_exception(*sys.exc_info())
        extra_info = extra_info + _error_string(e, trace, SERIALIZATION_VALIDATION_ERROR)

    return f"""
# Single QUA script generated at {datetime.datetime.now()}
# QUA library version: {version.__version__}

{serialized_program}
{extra_info if extra_info else ""}
config = {pretty_original_config}

loaded_config = {pretty_proto_config}

"""


def _validate_program(old_prog, serialized_program: str) -> Optional[str]:
    generated_mod = types.ModuleType("gen")
    exec(serialized_program, generated_mod.__dict__)
    new_prog = generated_mod.prog.build(QuaConfig())

    new_prog_str = _program_string(new_prog)
    old_prog_str = _program_string(old_prog)

    if new_prog_str != old_prog_str:
        if not _switched_strings(new_prog_str, old_prog_str):
            new_prog_str = new_prog_str.replace("\n", "")
            old_prog_str = old_prog_str.replace("\n", "")
            return f"""

####     {SERIALIZATION_NOT_COMPLETE}     ####
#
#  Original   {old_prog_str}
#  Serialized {new_prog_str}
#
################################################

        """

    return ""


def _switched_strings(prog1_str, prog2_str):
    """The created stream might be identical besides the ordering of the declared streams. The declared streams names
    format is either "r5" for a regular stream or "atr5" for a stream with "adc_trace=True". This function checks if
    the only difference in the strings are these name changes.
    """
    tag = r' *"tag": "(at)?r[\d]+"'
    string_value = r' *"stringValue": "(at)?r[\d]+"'
    prog1_str_split = prog1_str.splitlines()
    prog2_str_split = prog2_str.splitlines()
    if len(prog1_str_split) != len(prog2_str_split):
        return False
    for line1, line2 in zip(prog1_str_split, prog2_str_split):
        if line1 != line2:
            if not re.match(tag, line1) or not re.match(tag, line2):
                if not re.match(string_value, line1) or not re.match(string_value, line2):
                    return False
    return True


def _error_string(e: Exception, trace, error_type: str) -> str:
    return f"""

    ####     {error_type}     ####
    #
    #  {str(e)}
    #
    # Trace:
    #   {str(trace)}
    #
    ################################################

            """


def _program_string(prog) -> str:
    """Will create a canonized string representation of the program"""
    strip_location_visitor = _StripLocationVisitor()
    strip_location_visitor.visit(prog)
    string = prog.to_json(2)
    return string


def _print_config(config_part: Dict[str, Any], indent_level: int = 1) -> str:
    """Formats a python dictionary into an executable string representation.
    Unlike pretty print, it better supports nested dictionaries. Also, auto converts
    lists into a more compact form.
    Works recursively.
    :param Dict[str, Any] config_part: The dictionary to format

    Args:
        indent_level (int): Internally used by the function to indicate
            the current
    indention
    :returns str: The string representation of the dictionary.
    """
    if indent_level > 100:
        raise ConfigSerializationException("Reached maximum depth of config pretty print")

    config_part_str = ""
    if len(config_part) > 0:
        config_part_str += "{\n"

        for key, value in config_part.items():
            config_part_str += "    " * indent_level + f'"{str(key)}": ' + _value_to_str(indent_level, value)

        if indent_level > 1:
            # add an indentation and go down a line
            config_part_str += "    " * (indent_level - 1) + "},\n"
        else:
            # in root indent level, no need to add a line
            config_part_str += "}"

    else:
        config_part_str = "{},\n"

    return config_part_str


def _value_to_str(indent_level, value):
    # To support numpy types, we convert them to normal python types:
    if type(value).__module__ == np.__name__:
        value = value.tolist()

    is_long_list = isinstance(value, list) and len(value) > 1

    if isinstance(value, dict):
        return _print_config(value, indent_level + 1)
    elif isinstance(value, str):
        return f'"{value}"' + ",\n"
    elif is_long_list and isinstance(value[0], dict):
        temp_str = "[\n"
        for v in value:
            temp_str += "    " * (indent_level + 1) + f"{str(v)},\n"
        temp_str += "    " * indent_level + "],\n"
        return temp_str
    elif is_long_list:
        # replace it with a compact list
        is_single_value = len(set(value)) == 1

        if is_single_value:
            return f"[{value[0]}] * {len(value)}" + ",\n"
        else:
            return f"{_make_compact_string_from_list(value)}" + ",\n"
    else:
        # python basic data types string representation are valid python
        return str(value) + ",\n"


def _make_compact_string_from_list(list_data):
    """Turns a multi-value list into the most compact string representation of it,
    replacing identical consecutive values by list multiplication.
    """
    list_string = ""
    # Indices where the value changes
    changes_indices = []
    for i in range(len(list_data)):
        if (i == len(list_data) - 1) or (list_data[i + 1] != list_data[i]):
            changes_indices.append(i)

    prev_index = -1
    prev_number_of_identical = 0
    for curr_index in changes_indices:
        number_of_identical = curr_index - prev_index
        if prev_number_of_identical == 0:
            # First item on the list
            if number_of_identical == 1:
                list_string += f"[{list_data[curr_index]}"
            elif number_of_identical > 1:
                list_string += f"[{list_data[curr_index]}] * {number_of_identical}"
            else:
                raise ConfigSerializationException("number_of_identical can not be negative")

        else:
            if number_of_identical == 1 and prev_number_of_identical == 1:
                list_string += f", {list_data[curr_index]}"
            elif number_of_identical > 1 and prev_number_of_identical == 1:
                list_string += f"] + [{list_data[curr_index]}] * {number_of_identical}"
            elif number_of_identical == 1 and prev_number_of_identical > 1:
                list_string += f" + [{list_data[curr_index]}"
            elif number_of_identical > 1 and prev_number_of_identical > 1:
                list_string += f" + [{list_data[curr_index]}] * {number_of_identical}"
            else:
                raise ConfigSerializationException("number_of_identical can not be negative")

        prev_index = curr_index
        prev_number_of_identical = number_of_identical
    if prev_number_of_identical == 1:
        list_string += "]"
    return list_string


class _StripLocationVisitor(QuaNodeVisitor):
    """Go over all nodes and if they have a location property, we strip it"""

    def _default_enter(self, node):
        if hasattr(node, "loc"):
            node.loc = "stripped"
        return isinstance(node, betterproto.Message)

    @staticmethod
    def strip(node):
        _StripLocationVisitor().visit(node)
