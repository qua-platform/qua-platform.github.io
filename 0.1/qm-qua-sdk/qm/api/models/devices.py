from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Union

from qm.grpc.qm_api import DigitalInputPortPolarity


@dataclass(frozen=True)
class MixerInfo:
    mixer: str
    frequency_negative: bool
    intermediate_frequency: int = field(default=None)
    intermediate_frequency_double: float = field(default=None)
    lo_frequency: int = field(default=None)
    lo_frequency_double: float = field(default=None)

    def as_dict(self) -> Dict[str, Union[str, bool, int, float]]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class AnalogOutputPortFilter:
    feedforward: List[float]
    feedback: List[float]


class Polarity(Enum):
    RISING = DigitalInputPortPolarity.RISING
    FALLING = DigitalInputPortPolarity.FALLING
