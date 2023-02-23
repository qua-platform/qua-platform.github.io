import dataclasses
import logging
import time
from typing import (
    Type,
    Collection,
    Union,
    TYPE_CHECKING,
    TypeVar,
    Dict,
    Iterable,
    Callable,
)

import betterproto
import numpy as np
from deprecation import deprecated

from qm.grpc.general_messages import MessageLevel

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

T = TypeVar("T")


def fix_object_data_type(obj: T) -> T:
    if isinstance(obj, (np.floating, np.integer, np.bool_)):
        obj_item = obj.item()
        if type(obj_item) is np.longdouble:
            return float(obj_item)
        else:
            return obj_item
    else:
        return obj


_level_map = {
    MessageLevel.Message_LEVEL_ERROR: logging.ERROR,
    MessageLevel.Message_LEVEL_WARNING: logging.WARN,
    MessageLevel.Message_LEVEL_INFO: logging.INFO,
}


def get_all_iterable_data_types(it):
    return set([type(e) for e in it])


def collection_has_type(
    collection: Collection, type_to_check: Type, include_subclasses: bool
) -> bool:
    if include_subclasses:
        return any([isinstance(i, type_to_check) for i in collection])
    else:
        return any([type(i) is type_to_check for i in collection])


def collection_has_type_bool(collection: Collection):
    return collection_has_type(collection, bool, False) or collection_has_type(
        collection, np.bool_, True
    )


def collection_has_type_int(collection: Collection):
    return collection_has_type(collection, int, False) or collection_has_type(
        collection, np.integer, True
    )


def collection_has_type_float(collection: Collection):
    return collection_has_type(collection, float, False) or collection_has_type(
        collection, np.floating, True
    )


def is_iter(x):
    try:
        iter(x)
    except TypeError:
        return False
    else:
        return True


def get_iterable_elements_datatype(it):
    if isinstance(it, np.ndarray):
        return type(it[0].item())
    elif is_iter(it):
        if len(get_all_iterable_data_types(it)) > 1:
            raise ValueError("Multiple datatypes encounterd in iterable object")
        if isinstance(it[0], np.generic):
            return type(it[0].item())
        else:
            return type(it[0])
    else:
        return None


def list_fields(node) -> Dict[str, Union[betterproto.Message, Iterable]]:
    fields = dataclasses.fields(node)
    output = {}
    for field in fields:
        field_value = getattr(node, field.name)
        if isinstance(field_value, Iterable) or (
            isinstance(field_value, betterproto.Message)
            and betterproto.serialized_on_wire(field_value)
        ):
            output[field.name] = field_value
    return output


ValueType = TypeVar("ValueType")


def deprecate_to_property(
    value: ValueType, deprecated_in: str, removed_in: str, details: str
) -> ValueType:
    value_type = type(value)

    class DeprecatedProperty(value_type):
        @deprecated(deprecated_in, removed_in, details=details)
        def __call__(self, *args, **kwargs):
            return value_type(self)

    return DeprecatedProperty(value)


R = TypeVar("R")


def run_until_with_timeout(
    on_iteration_callback: Callable[[], bool],
    on_complete_callback: Callable[[], R] = lambda: None,
    timeout: float = float("infinity"),
    loop_interval: float = 0.1,
    timeout_message: str = "Timeout Exceeded",
) -> R:
    """

    :param on_iteration_callback: A callback that returns bool that is called every loop iteration.
     If True is returned, the loop is complete and on_complete_callback is called.

    :param on_complete_callback: A callback that is called when the loop is completed.
    This function returns the return value of on_complete_callback

    :param timeout: The timeout in seconds for on_iteration_callback to return True,
    on Zero the loop is executed once.

    :param loop_interval: The interval (in seconds) between each loop execution.

    :param timeout_message: The message of the TimeoutError exception.
    raise TimeoutError: When the timeout is exceeded
    """
    if timeout < 0:
        raise ValueError("timeout cannot be smaller than 0")

    start = time.time()
    end = start + timeout

    while True:
        if on_iteration_callback():
            return on_complete_callback()

        time.sleep(loop_interval)

        if time.time() >= end:
            raise TimeoutError(timeout_message)
