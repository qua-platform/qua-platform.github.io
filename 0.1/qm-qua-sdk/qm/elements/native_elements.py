from typing import List, Tuple, Union, Optional, Sequence, cast

import numpy
import betterproto
from dependency_injector.wiring import Provide, inject

from qm.api.frontend_api import FrontendApi
from qm.grpc.general_messages import Matrix
from qm.grpc.qua_config import QuaConfigDacPortReference
from qm.api.models.capabilities import ServerCapabilities
from qm.elements.basic_element import BasicElement, logger
from qm.api.models.devices import MixerInfo, AnalogOutputPortFilter
from qm.containers.capabilities_container import CapabilitiesContainer
from qm.type_hinting.general import NumpySupportedFloat, NumpySupportedNumber


def _set_single_output_port_dc_offset(
    frontend_api: FrontendApi,
    machine_id: str,
    element_name: str,
    input_name: str,
    offset: NumpySupportedNumber,
) -> None:
    offset = float(offset)
    logger.debug(f"Setting DC offset of input '{input_name}' on element '{element_name}' to '{offset}'")
    frontend_api.set_output_dc_offset(machine_id, element_name, input_name, offset)


def _create_taps_filter(
    feedforward: Union[Sequence[NumpySupportedFloat], None], feedback: Union[Sequence[NumpySupportedFloat], None]
) -> AnalogOutputPortFilter:
    for name, instance in zip(["feedforward", "feedback"], [feedforward, feedback]):
        if instance is not None and not isinstance(instance, (numpy.ndarray, List)):
            raise TypeError(f"{name} must be None, a list, or a numpy array. Got {type(instance)}.")
    if isinstance(feedforward, numpy.ndarray):
        feedforward = feedforward.tolist()
    if isinstance(feedback, numpy.ndarray):
        feedback = feedback.tolist()
    return AnalogOutputPortFilter(feedforward=cast(List[float], feedforward), feedback=cast(List[float], feedback))


@inject
def static_set_mixer_correction(
    frontend_api: FrontendApi,
    machine_id: str,
    mixer: str,
    intermediate_frequency: Union[int, float],
    lo_frequency: Union[int, float],
    values: Tuple[float, float, float, float],
    capabilities: ServerCapabilities = Provide[CapabilitiesContainer.capabilities],
) -> None:
    # TODO - this function is here (and not under MixedInputsElement) to support backwards the direct calling to mixer
    #  Once it is changed, one can put this function under the element

    if not isinstance(values, (tuple, list)) or len(values) != 4:
        raise Exception("correction values must have 4 items")

    float_values = [float(x) for x in values]
    correction_matrix = Matrix(*float_values)

    mixer_lo_frequency_double = 0.0
    mixer_intermediate_frequency_double = 0.0
    if capabilities.supports_double_frequency:
        mixer_lo_frequency_double = float(lo_frequency)
        mixer_intermediate_frequency_double = abs(float(intermediate_frequency))

    mixer_info = MixerInfo(
        mixer=mixer,
        frequency_negative=intermediate_frequency < 0,
        lo_frequency=int(lo_frequency),
        intermediate_frequency=abs(int(intermediate_frequency)),
        lo_frequency_double=mixer_lo_frequency_double,
        intermediate_frequency_double=mixer_intermediate_frequency_double,
    )
    frontend_api.set_correction(machine_id, mixer_info, correction_matrix)


class SingleInputElement(BasicElement):
    @property
    def port(self) -> QuaConfigDacPortReference:
        return self._config.single_input.port

    def set_output_dc_offset(self, offset: float) -> None:
        _set_single_output_port_dc_offset(self._frontend, self._id, self._name, "single", offset)

    def set_output_filter(
        self,
        feedforward: Union[Sequence[NumpySupportedFloat], None],
        feedback: Union[Sequence[NumpySupportedFloat], None],
    ) -> None:
        analog_filter = _create_taps_filter(feedforward, feedback)
        self._frontend.set_output_filter_taps(self._id, self._name, "single", analog_filter)


class MultipleInputsElement(BasicElement):
    pass


class SingleInputCollectionElement(BasicElement):
    pass


class MixInputsElement(BasicElement):
    @property
    def i_port(self) -> QuaConfigDacPortReference:
        return self._config.mix_inputs.i

    @property
    def q_port(self) -> QuaConfigDacPortReference:
        return self._config.mix_inputs.q

    @property
    @inject
    def lo_frequency(self, capabilities: ServerCapabilities = Provide[CapabilitiesContainer.capabilities]) -> float:
        if capabilities.supports_double_frequency:
            return self._config.mix_inputs.lo_frequency_double
        return self._config.mix_inputs.lo_frequency

    @lo_frequency.setter
    @inject
    def lo_frequency(
        self, value: float, capabilities: ServerCapabilities = Provide[CapabilitiesContainer.capabilities]
    ) -> None:
        freq = float(value)
        logger.debug(f"Setting element '{self._name}' intermediate frequency to '{freq}'.")
        self._config.mix_inputs.lo_frequency = int(freq)
        self._config.mix_inputs.lo_frequency_double = 0.0
        if capabilities.supports_double_frequency:
            self._config.mix_inputs.lo_frequency_double = float(freq)

    @property
    def mixer(self) -> str:
        return self._config.mix_inputs.mixer

    @property
    def has_octave_params(self) -> bool:
        return betterproto.serialized_on_wire(self._config.mix_inputs.octave_params)

    def set_output_dc_offset(self, i_offset: Optional[float] = None, q_offset: Optional[float] = None) -> None:
        if i_offset is not None:
            _set_single_output_port_dc_offset(self._frontend, self._id, self._name, "I", i_offset)
        if q_offset is not None:
            _set_single_output_port_dc_offset(self._frontend, self._id, self._name, "Q", q_offset)

    def set_output_filter(
        self,
        input_name: str,
        feedforward: Union[Sequence[NumpySupportedFloat], None],
        feedback: Union[Sequence[NumpySupportedFloat], None],
    ) -> None:
        analog_filter = _create_taps_filter(feedforward, feedback)
        self._frontend.set_output_filter_taps(
            self._id,
            self._name,
            input_name,
            analog_filter,
        )

    def set_mixer_correction(
        self,
        intermediate_frequency: int,
        lo_frequency: int,
        values: Tuple[float, float, float, float],
    ) -> None:
        static_set_mixer_correction(
            self._frontend,
            self._id,
            mixer=self.mixer,
            intermediate_frequency=intermediate_frequency,
            lo_frequency=lo_frequency,
            values=values,
        )
