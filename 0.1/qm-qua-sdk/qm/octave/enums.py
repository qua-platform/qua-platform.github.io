import warnings

from octave_sdk.octave import IFMode, ClockInfo
from octave_sdk import (
    ClockType,
    OctaveOutput,
    RFOutputMode,
    ClockFrequency,
    OctaveLOSource,
    RFInputLOSource,
    RFInputRFSource,
)

__all__ = [
    "RFInputRFSource",
    "RFOutputMode",
    "OctaveLOSource",
    "RFInputLOSource",
    "ClockType",
    "ClockFrequency",
    "OctaveOutput",
    "IFMode",
    "ClockInfo",
]

warnings.warn(
    "Octave enums should be directly imported from the octave_sdk "
    "(IFMode, and ClockInfo are imported from octave_sdk.octave), this file (qm.octave.enums)"
    "will be removed in the next version",
    category=DeprecationWarning,
)
