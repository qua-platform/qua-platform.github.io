# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: qm/grpc/quantum_simulator/v1/physical_system.proto
# plugin: python-betterproto
from dataclasses import dataclass
from typing import (
    Dict,
    List,
)

import betterproto


@dataclass(eq=False, repr=False)
class InputPort(betterproto.Message):
    """Input port of the quantum system (output port of OPX)"""

    controller: str = betterproto.string_field(1)
    """name of the controller"""

    id: int = betterproto.uint32_field(2)
    """id"""


@dataclass(eq=False, repr=False)
class OutputPort(betterproto.Message):
    """Output port of the quantum system (input port of OPX)"""

    controller: str = betterproto.string_field(1)
    """name of the controller"""

    id: int = betterproto.uint32_field(2)
    """id"""


@dataclass(eq=False, repr=False)
class TransmonProperties(betterproto.Message):
    """A class that holds the physical properties of a transmon."""

    frequency: float = betterproto.double_field(1)
    """frequency of the qubit in Hz"""

    anharmonicity: float = betterproto.double_field(2)
    """anharmonicity of the qubit in Hz"""

    t1: float = betterproto.double_field(3)
    """T1 time in ns"""

    t2: float = betterproto.double_field(4)
    """T2 time in ns"""

    n_levels: int = betterproto.uint32_field(5)
    n_order: int = betterproto.uint32_field(6)


@dataclass(eq=False, repr=False)
class IqMixerIn(betterproto.Message):
    """IQMixer for up conversion"""

    i: "InputPort" = betterproto.message_field(1)
    """output port of the OPX"""

    q: "InputPort" = betterproto.message_field(2)
    """output port of the OPX"""

    lo_frequency: float = betterproto.double_field(3)
    """frequency of the local oscillator in Hz"""


@dataclass(eq=False, repr=False)
class IqMixerOut(betterproto.Message):
    """IQMixer for down conversion"""

    i: "OutputPort" = betterproto.message_field(1)
    """input port of the OPX"""

    q: "OutputPort" = betterproto.message_field(2)
    """input port of the OPX"""

    lo_frequency: float = betterproto.double_field(3)
    """frequency of the local oscillator in Hz"""


@dataclass(eq=False, repr=False)
class AnalogFrontend(betterproto.Message):
    """
    A class to describe analog frontend (currently just a constant
    multiplicative factor)
    """

    amp_factor: float = betterproto.double_field(1)
    """
    a constant factor to account for losses or amplification of the signal
    """


@dataclass(eq=False, repr=False)
class FluxLine(betterproto.Message):
    """
    A class to describe flux line and how it is connected to the OPX. The
    frequency of the qubit follows is tuned as: amp*(flux voltage - offset)^2
    """

    port: "InputPort" = betterproto.message_field(1)
    """output port of the OPX driving the flux line"""

    amp_factor: float = betterproto.double_field(2)
    """amplitude in units of GHz/V^2"""

    offset: float = betterproto.double_field(3)
    """offset voltage at which the bias is zero"""


@dataclass(eq=False, repr=False)
class FixedFrequencyTransmon(betterproto.Message):
    pass


@dataclass(eq=False, repr=False)
class TunableFrequencyTransmon(betterproto.Message):
    """A class to describe tunable frequency transmon"""

    flux_line: "FluxLine" = betterproto.message_field(1)
    """flux line controlling the transmon frequency"""


@dataclass(eq=False, repr=False)
class Transmon(betterproto.Message):
    """
    Transmon contains the physical properties of the transmonand the
    information about how it is connected to the IQ Mixer and OPX
    """

    properties: "TransmonProperties" = betterproto.message_field(1)
    """physical properties of the transmon"""

    i_q_mixer: "IqMixerIn" = betterproto.message_field(2)
    """IQ mixer used to drive the qubit"""

    analog_frontend: "AnalogFrontend" = betterproto.message_field(3)
    """analog frontend"""

    fixed_frequency_transmon: "FixedFrequencyTransmon" = betterproto.message_field(
        4, group="type"
    )
    """fixed frequency qubit"""

    tunable_frequency_transmon: "TunableFrequencyTransmon" = betterproto.message_field(
        5, group="type"
    )
    """tunable frequency qubit"""


@dataclass(eq=False, repr=False)
class DriveResonator(betterproto.Message):
    pass


@dataclass(eq=False, repr=False)
class ReadoutResonator(betterproto.Message):
    """
    A class with the information about how the back reflected from the
    resonator is fed to the OPX.
    """

    i_q_mixer: "IqMixerOut" = betterproto.message_field(1)


@dataclass(eq=False, repr=False)
class ResonatorProperties(betterproto.Message):
    frequency: float = betterproto.double_field(1)
    """resonator frequency in Hz"""

    lossrate: float = betterproto.double_field(2)
    """resonator loss rate in Hz"""

    n_levels: int = betterproto.uint32_field(3)
    """number of n_levels"""


@dataclass(eq=False, repr=False)
class Resonator(betterproto.Message):
    """
    A class to describe the physical properties of readout resonator and how it
    is connected to the OPX
    """

    properties: "ResonatorProperties" = betterproto.message_field(1)
    i_q_mixer: "IqMixerIn" = betterproto.message_field(2)
    """IQMixer to upconvert the drive"""

    analog_frontend: "AnalogFrontend" = betterproto.message_field(3)
    """analog frontend"""

    drive_resonator: "DriveResonator" = betterproto.message_field(4, group="type")
    """drive resonator"""

    readout_resonator: "ReadoutResonator" = betterproto.message_field(5, group="type")
    """readout resonator"""


@dataclass(eq=False, repr=False)
class CapacitiveCoupler(betterproto.Message):
    """A class for describing capacitive coupling between two qubits"""

    g: "InputPort" = betterproto.message_field(1)
    """output port of the OPX driving the coupler"""

    amp_factor: float = betterproto.double_field(2)
    """amplitude factor in units of GHz/V"""


@dataclass(eq=False, repr=False)
class TransmonTransmonCoupling(betterproto.Message):
    """Transmon-transmon coupling"""

    capacitive_coupler: str = betterproto.string_field(1)
    """name of the capacitive coupler"""

    qb1: str = betterproto.string_field(2)
    """name of the qubit 1"""

    qb2: str = betterproto.string_field(3)
    """name of the qubit 2"""


@dataclass(eq=False, repr=False)
class TransmonResonatorCoupling(betterproto.Message):
    """
    Transmon-resonator coupling describes the connectivity between a qubit and
    a resonator
    """

    transmon: str = betterproto.string_field(1)
    """name of the qubit"""

    resonator: str = betterproto.string_field(2)
    """name of the resonator"""

    g: float = betterproto.double_field(3)
    """strength of the coupling in GHz"""

    is_dispersive: bool = betterproto.bool_field(4)
    """coupling type"""


@dataclass(eq=False, repr=False)
class ScChip(betterproto.Message):
    """
    A class to describe a superconducting chip layout consisting of fixed/flux
    tunable transmons, capacitive couplers and readout resonators.
    """

    transmons: Dict[str, "Transmon"] = betterproto.map_field(
        1, betterproto.TYPE_STRING, betterproto.TYPE_MESSAGE
    )
    """a dictionary of Transmons"""

    resonators: Dict[str, "Resonator"] = betterproto.map_field(
        2, betterproto.TYPE_STRING, betterproto.TYPE_MESSAGE
    )
    """a dictionary of resonators"""

    capacitive_couplers: Dict[str, "CapacitiveCoupler"] = betterproto.map_field(
        3, betterproto.TYPE_STRING, betterproto.TYPE_MESSAGE
    )
    """a dictionary of capacitive couplers"""

    transmon_transmon_coupling: List[
        "TransmonTransmonCoupling"
    ] = betterproto.message_field(4)
    """a list containing all the qubit-qubit couplings in the chip"""

    transmon_resonator_coupling: List[
        "TransmonResonatorCoupling"
    ] = betterproto.message_field(5)
    """
    a list containing the qubit-resonator couplings and their respective
    strengths
    """


@dataclass(eq=False, repr=False)
class Offset(betterproto.Message):
    port: "InputPort" = betterproto.message_field(1)
    value: float = betterproto.double_field(2)


@dataclass(eq=False, repr=False)
class Waveform(betterproto.Message):
    constant_waveform: "ConstantWaveform" = betterproto.message_field(1, group="type")
    arbitrary_waveform: "ArbitraryWaveform" = betterproto.message_field(2, group="type")


@dataclass(eq=False, repr=False)
class ConstantWaveform(betterproto.Message):
    sample: float = betterproto.double_field(1)


@dataclass(eq=False, repr=False)
class ArbitraryWaveform(betterproto.Message):
    samples: List[float] = betterproto.double_field(1)


@dataclass(eq=False, repr=False)
class Error(betterproto.Message):
    type: str = betterproto.string_field(1)
    stack: str = betterproto.string_field(2)


@dataclass(eq=False, repr=False)
class ColdAtomDevice(betterproto.Message):
    v: float = betterproto.double_field(1)
    qubit: str = betterproto.string_field(2)
    frequency_01: float = betterproto.double_field(3)
    frequency_1_r: float = betterproto.double_field(4)
    positions: List["Coordinate"] = betterproto.message_field(5)
    t1: float = betterproto.double_field(6)
    t2: float = betterproto.double_field(7)


@dataclass(eq=False, repr=False)
class Coordinate(betterproto.Message):
    x: float = betterproto.double_field(1)
    y: float = betterproto.double_field(2)


@dataclass(eq=False, repr=False)
class ColdAtomSetup(betterproto.Message):
    device: "ColdAtomDevice" = betterproto.message_field(1)
    global_raman_beam: "GlobalRamanBeam" = betterproto.message_field(2)
    global_rydberg_beam: "GlobalRydbergBeam" = betterproto.message_field(3)
    local_raman_detuning: "AcStarkShifter" = betterproto.message_field(4)
    local_rydberg_detuning: "AcStarkShifter" = betterproto.message_field(5)


@dataclass(eq=False, repr=False)
class BeamSteerer(betterproto.Message):
    aod_x: str = betterproto.string_field(1)
    aod_y: str = betterproto.string_field(2)
    reference_position: "Coordinate" = betterproto.message_field(3)
    eta_x: float = betterproto.double_field(4)
    eta_y: float = betterproto.double_field(5)


@dataclass(eq=False, repr=False)
class AcStarkShifter(betterproto.Message):
    aom: str = betterproto.string_field(1)
    delta: float = betterproto.double_field(2)
    eta_x: List[float] = betterproto.double_field(3)
    beam_steerer: "BeamSteerer" = betterproto.message_field(4)


@dataclass(eq=False, repr=False)
class GlobalRamanBeam(betterproto.Message):
    intensity_modulator: str = betterproto.string_field(1)
    frequency: float = betterproto.double_field(2)
    scale_factor: float = betterproto.double_field(3)
    lo_frequency: float = betterproto.double_field(4)


@dataclass(eq=False, repr=False)
class GlobalRydbergBeam(betterproto.Message):
    aom1: str = betterproto.string_field(1)
    aom2: str = betterproto.string_field(2)
    frequency1: float = betterproto.double_field(3)
    frequency2: float = betterproto.double_field(4)
    scale_factor1: float = betterproto.double_field(5)
    scale_factor2: float = betterproto.double_field(6)


@dataclass(eq=False, repr=False)
class PhysicalConfig(betterproto.Message):
    chip: "ScChip" = betterproto.message_field(1, group="type")
    cold_atom_setup: "ColdAtomSetup" = betterproto.message_field(2, group="type")
