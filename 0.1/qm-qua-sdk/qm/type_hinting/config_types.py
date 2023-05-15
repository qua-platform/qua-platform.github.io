from typing_extensions import TypedDict
from typing import Dict, List, Tuple, Union

from qm.type_hinting.general import Number

PortReferenceType = Tuple[str, int]


# TODO: This is a placeholder while we still use dicts, once we move to pydantics we can simply change the
#  inheritance of the classes handled here and add a more robust validation to the types


class AnalogOutputFilterConfigType(TypedDict, total=False):
    feedforward: List[float]
    feedback: List[float]


class AnalogOutputPortConfigType(TypedDict, total=False):
    offset: Number
    filter: AnalogOutputFilterConfigType
    delay: int
    crosstalk: Dict[int, Number]
    shareable: bool
    connectivity: Tuple[str, str]


class AnalogInputPortConfigType(TypedDict, total=False):
    offset: Number
    gain_db: int
    shareable: bool
    connectivity: Tuple[str, str]


class DigitalOutputPortConfigType(TypedDict, total=False):
    sharable: bool
    inverted: bool
    connectivity: Tuple[str, str]


class DigitalInputPortConfigType(TypedDict, total=False):
    deadtime: int
    polarity: str
    threshold: Number
    connectivity: Tuple[str, str]


class ControllerConfigType(TypedDict, total=False):
    type: str
    analog_outputs: Dict[int, AnalogOutputPortConfigType]
    analog_inputs: Dict[int, AnalogInputPortConfigType]
    digital_outputs: Dict[int, DigitalOutputPortConfigType]
    digital_inputs: Dict[int, DigitalInputPortConfigType]
    connectivity: str


class OctaveConfigType(TypedDict, total=False):
    loopbacks: List[Tuple[Tuple[str, str], str]]


class DigitalInputConfigType(TypedDict, total=False):
    delay: int
    buffer: int
    port: PortReferenceType


class IntegrationWeightConfigType(TypedDict, total=False):
    cosine: Union[List[Tuple[float, int]], List[float]]
    sine: Union[List[Tuple[float, int]], List[float]]


class ConstantWaveFormConfigType(TypedDict, total=False):
    type: str
    sample: float


class ArbitraryWaveFormConfigType(TypedDict, total=False):
    type: str
    samples: List[float]
    max_allowed_error: float
    sampling_rate: Number
    is_overridable: bool


class DigitalWaveformConfigType(TypedDict, total=False):
    samples: List[Tuple[int, int]]


class MixerConfigType(TypedDict, total=False):
    intermediate_frequency: float
    lo_frequency: float
    correction: Tuple[Number, Number, Number, Number]


class PulseConfigType(TypedDict, total=False):
    operation: str
    length: int
    waveforms: Dict[str, str]
    digital_marker: str
    integration_weights: Dict[str, str]


class SingleInputConfigType(TypedDict, total=False):
    port: PortReferenceType


class HoldOffsetConfigType(TypedDict, total=False):
    duration: int


class MixInputOctaveParamsConfigType(TypedDict, total=False):
    rf_output_port: Tuple[str, str]
    lo_source: str
    output_switch_state: str
    output_gain: int
    downconversion_lo_source: str
    downconversion_lo_frequency: float
    rf_input_port: Tuple[str, str]


class StickyConfigType(TypedDict, total=False):
    analog: bool
    digital: bool
    duration: int


class MixInputConfigType(TypedDict, total=False):
    I: PortReferenceType
    Q: PortReferenceType
    mixer: str
    lo_frequency: float
    octave_params: MixInputOctaveParamsConfigType


class InputCollectionConfigType(TypedDict, total=False):
    inputs: Dict[str, PortReferenceType]


class OscillatorConfigType(TypedDict, total=False):
    intermediate_frequency: float
    mixer: str
    lo_frequency: float


class OutputPulseParameterConfigType(TypedDict):
    signalThreshold: int
    signalPolarity: str
    derivativeThreshold: int
    derivativePolarity: str


class ElementConfigType(TypedDict, total=False):
    intermediate_frequency: float
    oscillator: str
    measurement_qe: str
    operations: Dict[str, str]
    singleInput: SingleInputConfigType
    mixInputs: MixInputConfigType
    singleInputCollection: InputCollectionConfigType
    multipleInputs: InputCollectionConfigType
    time_of_flight: int
    smearing: int
    outputs: Dict[str, PortReferenceType]
    digitalInputs: Dict[str, DigitalInputConfigType]
    digitalOutputs: Dict[str, PortReferenceType]
    outputPulseParameters: OutputPulseParameterConfigType
    hold_offset: HoldOffsetConfigType
    sticky: StickyConfigType
    thread: str


class DictQuaConfig(TypedDict, total=False):
    version: int
    oscillators: Dict[str, OscillatorConfigType]
    elements: Dict[str, ElementConfigType]
    controllers: Dict[str, ControllerConfigType]
    octaves: Dict[str, OctaveConfigType]
    integration_weights: Dict[str, IntegrationWeightConfigType]
    waveforms: Dict[str, Union[ArbitraryWaveFormConfigType, ConstantWaveFormConfigType]]
    digital_waveforms: Dict[str, DigitalWaveformConfigType]
    pulses: Dict[str, PulseConfigType]
    mixers: Dict[str, List[MixerConfigType]]
