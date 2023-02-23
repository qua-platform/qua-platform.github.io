import dataclasses
from enum import Enum, auto
from typing import Optional

try:
    from octave_sdk import (
        RFInputRFSource as sdk_RFInputRFSource,
        RFOutputMode as sdk_RFOutputMode,
        OctaveLOSource as sdk_OctaveLOSource,
        RFInputLOSource as sdk_RFInputLOSource,
        ClockType as sdk_ClockType,
        ClockFrequency as sdk_ClockFrequency,
        OctaveOutput as sdk_OctaveOutput,
    )
    from octave_sdk.octave import IFMode as sdk_IFMode
except ModuleNotFoundError:
    # Setting empty values for tests
    sdk_OctaveLOSource = None
    sdk_OctaveOutput = None
    sdk_RFInputRFSource = None
    sdk_RFOutputMode = None
    sdk_RFInputLOSource = None
    sdk_ClockType = None
    sdk_ClockFrequency = None


class RFInputRFSource(Enum):
    """"""

    RF_in = auto()
    Loopback_RF_out_1 = auto()
    Loopback_RF_out_2 = auto()
    Loopback_RF_out_3 = auto()
    Loopback_RF_out_4 = auto()
    Loopback_RF_out_5 = auto()
    Off = auto()

    def to_sdk(self):
        if self == RFInputRFSource.RF_in:
            return sdk_RFInputRFSource.RF_in
        elif self == RFInputRFSource.Off:
            return sdk_RFInputRFSource.Off
        elif self == RFInputRFSource.Loopback_RF_out_1:
            return sdk_RFInputRFSource.Loopback_RF_out_1
        elif self == RFInputRFSource.Loopback_RF_out_2:
            return sdk_RFInputRFSource.Loopback_RF_out_2
        elif self == RFInputRFSource.Loopback_RF_out_3:
            return sdk_RFInputRFSource.Loopback_RF_out_3
        elif self == RFInputRFSource.Loopback_RF_out_4:
            return sdk_RFInputRFSource.Loopback_RF_out_4
        elif self == RFInputRFSource.Loopback_RF_out_5:
            return sdk_RFInputRFSource.Loopback_RF_out_5
        else:
            return None

    @staticmethod
    def from_sdk(value):
        if value == sdk_RFInputRFSource.RF_in:
            return RFInputRFSource.RF_in
        elif value == sdk_RFInputRFSource.Off:
            return RFInputRFSource.Off
        elif value == sdk_RFInputRFSource.Loopback_RF_out_1:
            return RFInputRFSource.Loopback_RF_out_1
        elif value == sdk_RFInputRFSource.Loopback_RF_out_2:
            return RFInputRFSource.Loopback_RF_out_2
        elif value == sdk_RFInputRFSource.Loopback_RF_out_3:
            return RFInputRFSource.Loopback_RF_out_3
        elif value == sdk_RFInputRFSource.Loopback_RF_out_4:
            return RFInputRFSource.Loopback_RF_out_4
        elif value == sdk_RFInputRFSource.Loopback_RF_out_5:
            return RFInputRFSource.Loopback_RF_out_5
        else:
            raise ValueError(f"Clock type {value} is unknown")


class IFMode(Enum):
    """"""

    direct = auto()
    envelope = auto()
    mixer = auto()
    off = auto()

    def to_sdk(self):
        if self == IFMode.direct:
            return sdk_IFMode.direct
        elif self == IFMode.envelope:
            return sdk_IFMode.envelope
        elif self == IFMode.mixer:
            return sdk_IFMode.mixer
        elif self == IFMode.off:
            return sdk_IFMode.off
        else:
            return None

    @staticmethod
    def from_sdk(value):
        if value == sdk_IFMode.direct:
            return IFMode.direct
        elif value == sdk_IFMode.envelope:
            return IFMode.envelope
        elif value == sdk_IFMode.mixer:
            return IFMode.mixer
        elif value == sdk_IFMode.off:
            return IFMode.off
        else:
            raise ValueError(f"Clock type {value} is unknown")


class RFOutputMode(Enum):
    """"""

    trig_normal = auto()
    trig_inverse = auto()
    on = auto()
    off = auto()
    debug = auto()

    def to_sdk(self):
        if self == RFOutputMode.trig_normal:
            return sdk_RFOutputMode.trig_normal
        elif self == RFOutputMode.trig_inverse:
            return sdk_RFOutputMode.trig_inverse
        elif self == RFOutputMode.on:
            return sdk_RFOutputMode.on
        elif self == RFOutputMode.off:
            return sdk_RFOutputMode.off
        elif self == RFOutputMode.debug:
            return sdk_RFOutputMode.debug
        else:
            return None

    @staticmethod
    def from_sdk(value):
        if value == sdk_RFOutputMode.trig_normal:
            return RFOutputMode.trig_normal
        elif value == sdk_RFOutputMode.trig_inverse:
            return RFOutputMode.trig_inverse
        elif value == sdk_RFOutputMode.on:
            return RFOutputMode.on
        elif value == sdk_RFOutputMode.off:
            return RFOutputMode.off
        elif value == sdk_RFOutputMode.debug:
            return RFOutputMode.debug
        else:
            raise ValueError(f"Clock type {value} is unknown")


class OctaveLOSource(Enum):
    """input to the octave, uses it for output"""

    Off = auto()
    Internal = auto()
    Dmd1LO = auto()
    Dmd2LO = auto()
    LO1 = auto()
    LO2 = auto()
    LO3 = auto()
    LO4 = auto()
    LO5 = auto()
    RF_IN1 = auto()
    RF_IN2 = auto()
    IF1_LO_I = auto()
    IF1_LO_Q = auto()
    IF2_LO_I = auto()
    IF2_LO_Q = auto()

    def to_sdk(self):
        if self == OctaveLOSource.Off:
            return sdk_OctaveLOSource.Off
        elif self == OctaveLOSource.Internal:
            return sdk_OctaveLOSource.Internal
        elif self == OctaveLOSource.Dmd1LO:
            return sdk_OctaveLOSource.Dmd1LO
        elif self == OctaveLOSource.Dmd2LO:
            return sdk_OctaveLOSource.Dmd2LO
        elif self == OctaveLOSource.LO1:
            return sdk_OctaveLOSource.LO1
        elif self == OctaveLOSource.LO2:
            return sdk_OctaveLOSource.LO2
        elif self == OctaveLOSource.LO3:
            return sdk_OctaveLOSource.LO3
        elif self == OctaveLOSource.LO4:
            return sdk_OctaveLOSource.LO4
        elif self == OctaveLOSource.LO5:
            return sdk_OctaveLOSource.LO5
        elif self == OctaveLOSource.RF_IN1:
            return sdk_OctaveLOSource.RF_IN1
        elif self == OctaveLOSource.RF_IN2:
            return sdk_OctaveLOSource.RF_IN2
        elif self == OctaveLOSource.IF1_LO_I:
            return sdk_OctaveLOSource.IF1_LO_I
        elif self == OctaveLOSource.IF1_LO_Q:
            return sdk_OctaveLOSource.IF1_LO_Q
        elif self == OctaveLOSource.IF2_LO_I:
            return sdk_OctaveLOSource.IF2_LO_I
        elif self == OctaveLOSource.IF2_LO_Q:
            return sdk_OctaveLOSource.IF2_LO_Q
        else:
            return None

    @staticmethod
    def from_sdk(value):
        if value == sdk_OctaveLOSource.Off:
            return OctaveLOSource.Off
        elif value == sdk_OctaveLOSource.Internal:
            return OctaveLOSource.Internal
        elif value == sdk_OctaveLOSource.Dmd1LO:
            return OctaveLOSource.Dmd1LO
        elif value == sdk_OctaveLOSource.Dmd2LO:
            return OctaveLOSource.Dmd2LO
        elif value == sdk_OctaveLOSource.LO1:
            return OctaveLOSource.LO1
        elif value == sdk_OctaveLOSource.LO2:
            return OctaveLOSource.LO2
        elif value == sdk_OctaveLOSource.LO3:
            return OctaveLOSource.LO3
        elif value == sdk_OctaveLOSource.LO4:
            return OctaveLOSource.LO4
        elif value == sdk_OctaveLOSource.LO5:
            return OctaveLOSource.LO5
        elif value == sdk_OctaveLOSource.RF_IN1:
            return OctaveLOSource.RF_IN1
        elif value == sdk_OctaveLOSource.RF_IN2:
            return OctaveLOSource.RF_IN2
        elif value == sdk_OctaveLOSource.IF1_LO_I:
            return OctaveLOSource.IF1_LO_I
        elif value == sdk_OctaveLOSource.IF1_LO_Q:
            return OctaveLOSource.IF1_LO_Q
        elif value == sdk_OctaveLOSource.IF2_LO_I:
            return OctaveLOSource.IF2_LO_I
        elif value == sdk_OctaveLOSource.IF2_LO_Q:
            return OctaveLOSource.IF2_LO_Q
        else:
            raise ValueError(f"Clock type {value} is unknown")


class RFInputLOSource(Enum):
    """input to octave, uses it for downconversion, the lo
    extending the OctaveLOSourceInput
    """

    Off = auto()
    Internal = auto()
    Dmd1LO = auto()
    Dmd2LO = auto()
    LO1 = auto()
    LO2 = auto()
    LO3 = auto()
    LO4 = auto()
    LO5 = auto()
    Analyzer = auto()
    RFOutput1_LO = auto()
    RFOutput2_LO = auto()
    RFOutput3_LO = auto()
    RFOutput4_LO = auto()
    RFOutput5_LO = auto()

    def to_sdk(self):
        if self == RFInputLOSource.Off:
            return sdk_RFInputLOSource.Off
        elif self == RFInputLOSource.Internal:
            return sdk_RFInputLOSource.Internal
        elif self == RFInputLOSource.Dmd1LO:
            return sdk_RFInputLOSource.Dmd1LO
        elif self == RFInputLOSource.Dmd2LO:
            return sdk_RFInputLOSource.Dmd2LO
        elif self == RFInputLOSource.LO1:
            return sdk_RFInputLOSource.LO1
        elif self == RFInputLOSource.LO2:
            return sdk_RFInputLOSource.LO2
        elif self == RFInputLOSource.LO3:
            return sdk_RFInputLOSource.LO3
        elif self == RFInputLOSource.LO4:
            return sdk_RFInputLOSource.LO4
        elif self == RFInputLOSource.LO5:
            return sdk_RFInputLOSource.LO5
        elif self == RFInputLOSource.Analyzer:
            return sdk_RFInputLOSource.Analyzer
        elif self == RFInputLOSource.RFOutput1_LO:
            return sdk_RFInputLOSource.RFOutput1_LO
        elif self == RFInputLOSource.RFOutput2_LO:
            return sdk_RFInputLOSource.RFOutput2_LO
        elif self == RFInputLOSource.RFOutput3_LO:
            return sdk_RFInputLOSource.RFOutput3_LO
        elif self == RFInputLOSource.RFOutput4_LO:
            return sdk_RFInputLOSource.RFOutput4_LO
        elif self == RFInputLOSource.RFOutput5_LO:
            return sdk_RFInputLOSource.RFOutput5_LO
        else:
            return None

    @staticmethod
    def from_sdk(value):
        if value == sdk_RFInputLOSource.Off:
            return RFInputLOSource.Off
        elif value == sdk_RFInputLOSource.Internal:
            return RFInputLOSource.Internal
        elif value == sdk_RFInputLOSource.Dmd1LO:
            return RFInputLOSource.Dmd1LO
        elif value == sdk_RFInputLOSource.Dmd2LO:
            return RFInputLOSource.Dmd2LO
        elif value == sdk_RFInputLOSource.LO1:
            return RFInputLOSource.LO1
        elif value == sdk_RFInputLOSource.LO2:
            return RFInputLOSource.LO2
        elif value == sdk_RFInputLOSource.LO3:
            return RFInputLOSource.LO3
        elif value == sdk_RFInputLOSource.LO4:
            return RFInputLOSource.LO4
        elif value == sdk_RFInputLOSource.LO5:
            return RFInputLOSource.LO5
        elif value == sdk_RFInputLOSource.Analyzer:
            return RFInputLOSource.Analyzer
        elif value == sdk_RFInputLOSource.RFOutput1_LO:
            return RFInputLOSource.RFOutput1_LO
        elif value == sdk_RFInputLOSource.RFOutput2_LO:
            return RFInputLOSource.RFOutput2_LO
        elif value == sdk_RFInputLOSource.RFOutput3_LO:
            return RFInputLOSource.RFOutput3_LO
        elif value == sdk_RFInputLOSource.RFOutput4_LO:
            return RFInputLOSource.RFOutput4_LO
        elif value == sdk_RFInputLOSource.RFOutput5_LO:
            return RFInputLOSource.RFOutput5_LO
        else:
            raise ValueError(f"Clock type {value} is unknown")


class ClockType(Enum):
    """"""

    Internal = auto()
    External = auto()
    Buffered = auto()  # for opt

    def to_sdk(self):
        if self == ClockType.Internal:
            return sdk_ClockType.Internal
        elif self == ClockType.Buffered:
            return sdk_ClockType.Buffered
        elif self == ClockType.External:
            return sdk_ClockType.External
        else:
            return None

    @staticmethod
    def from_sdk(value):
        if value == sdk_ClockType.Internal:
            return ClockType.Internal
        elif value == sdk_ClockType.Buffered:
            return ClockType.Buffered
        elif value == sdk_ClockType.External:
            return ClockType.External
        else:
            raise ValueError(f"Clock type {value} is unknown")


class ClockFrequency(Enum):
    """"""

    MHZ_10 = auto()
    MHZ_100 = auto()
    MHZ_1000 = auto()

    def to_sdk(self):
        if self == ClockFrequency.MHZ_10:
            return sdk_ClockFrequency.MHZ_10
        elif self == ClockFrequency.MHZ_100:
            return sdk_ClockFrequency.MHZ_100
        elif self == ClockFrequency.MHZ_1000:
            return sdk_ClockFrequency.MHZ_1000
        else:
            return None

    @staticmethod
    def from_sdk(value):
        if value == sdk_ClockFrequency.MHZ_10:
            return ClockFrequency.MHZ_10
        elif value == sdk_ClockFrequency.MHZ_100:
            return ClockFrequency.MHZ_100
        elif value == sdk_ClockFrequency.MHZ_1000:
            return ClockFrequency.MHZ_1000
        else:
            raise ValueError(f"Clock type {value} is unknown")


class OctaveOutput(Enum):
    Synth1 = auto()
    Synth2 = auto()
    Synth3 = auto()
    Synth4 = auto()
    Synth5 = auto()
    RF1 = auto()
    RF2 = auto()
    RF3 = auto()
    RF4 = auto()
    RF5 = auto()
    IF_OUT1 = auto()
    IF_OUT2 = auto()
    Dig1 = auto()
    Dig2 = auto()
    Dig3 = auto()

    def to_sdk(self):
        if self == OctaveOutput.Synth1:
            return sdk_OctaveOutput.Synth1
        elif self == OctaveOutput.Synth2:
            return sdk_OctaveOutput.Synth2
        elif self == OctaveOutput.Synth3:
            return sdk_OctaveOutput.Synth3
        elif self == OctaveOutput.Synth4:
            return sdk_OctaveOutput.Synth4
        elif self == OctaveOutput.Synth5:
            return sdk_OctaveOutput.Synth5
        elif self == OctaveOutput.RF1:
            return sdk_OctaveOutput.RF1
        elif self == OctaveOutput.RF2:
            return sdk_OctaveOutput.RF2
        elif self == OctaveOutput.RF3:
            return sdk_OctaveOutput.RF3
        elif self == OctaveOutput.RF4:
            return sdk_OctaveOutput.RF4
        elif self == OctaveOutput.RF5:
            return sdk_OctaveOutput.RF5
        elif self == OctaveOutput.IF_OUT1:
            return sdk_OctaveOutput.IF_OUT1
        elif self == OctaveOutput.IF_OUT2:
            return sdk_OctaveOutput.IF_OUT2
        elif self == OctaveOutput.Dig1:
            return sdk_OctaveOutput.Dig1
        elif self == OctaveOutput.Dig2:
            return sdk_OctaveOutput.Dig2
        elif self == OctaveOutput.Dig3:
            return sdk_OctaveOutput.Dig3
        else:
            return None

    @staticmethod
    def from_sdk(value):
        if value == sdk_OctaveOutput.Synth1:
            return OctaveOutput.Synth1
        elif value == sdk_OctaveOutput.Synth2:
            return OctaveOutput.Synth2
        elif value == sdk_OctaveOutput.Synth3:
            return OctaveOutput.Synth3
        elif value == sdk_OctaveOutput.Synth4:
            return OctaveOutput.Synth4
        elif value == sdk_OctaveOutput.Synth5:
            return OctaveOutput.Synth5
        elif value == sdk_OctaveOutput.RF1:
            return OctaveOutput.RF1
        elif value == sdk_OctaveOutput.RF2:
            return OctaveOutput.RF2
        elif value == sdk_OctaveOutput.RF3:
            return OctaveOutput.RF3
        elif value == sdk_OctaveOutput.RF4:
            return OctaveOutput.RF4
        elif value == sdk_OctaveOutput.RF5:
            return OctaveOutput.RF5
        elif value == sdk_OctaveOutput.IF_OUT1:
            return OctaveOutput.IF_OUT1
        elif value == sdk_OctaveOutput.IF_OUT2:
            return OctaveOutput.IF_OUT2
        elif value == sdk_OctaveOutput.Dig1:
            return OctaveOutput.Dig1
        elif value == sdk_OctaveOutput.Dig2:
            return OctaveOutput.Dig2
        elif value == sdk_OctaveOutput.Dig3:
            return OctaveOutput.Dig3
        else:
            raise ValueError(f"Clock type {value} is unknown")


@dataclasses.dataclass
class ClockInfo:
    clock_type: ClockType
    frequency: Optional[ClockFrequency]
