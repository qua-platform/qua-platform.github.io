from typing import Dict, Optional

import betterproto
from octave_sdk import Octave, OctaveOutput, OctaveLOSource  # type: ignore[import]

from qm.octave import QmOctaveConfig
from qm.api.frontend_api import FrontendApi
from qm.elements.basic_element import BasicElement
from qm.elements.element_with_octave import ElementWithOctave
from qm.grpc.octave_models import OctaveIfInputPort, OctaveIfInputPortName
from qm.elements.native_elements import (
    MixInputsElement,
    SingleInputElement,
    MultipleInputsElement,
    SingleInputCollectionElement,
)
from qm.grpc.qua_config import (
    QuaConfig,
    QuaConfigMixInputs,
    QuaConfigSingleInput,
    QuaConfigMultipleInputs,
    QuaConfigDacPortReference,
    QuaConfigSingleInputCollection,
)

MaybeOctaveInputPort = Optional[OctaveIfInputPort]


class ElementNotFound(KeyError):
    def __init__(self, key: str):
        self._key = key

    def __str__(self) -> str:
        return f"Element with the key {self._key} was not found."


class UnknownElementType(ValueError):
    pass


class OctaveLoopbackError(Exception):
    pass


class OctaveConnectionError(Exception):
    def __init__(self, i_port: MaybeOctaveInputPort, q_port: MaybeOctaveInputPort):
        self._i = i_port
        self._q = q_port


class OnlyOneConnectedPort(OctaveConnectionError):
    def __str__(self) -> str:
        connected_port = self._i or self._q
        assert isinstance(connected_port, OctaveIfInputPort)
        return (
            f"Only {connected_port.port_name.name} is connected to octave, while the other isn't. "
            f"Either both of them should be connected, or none of them"
        )


class DifferentOctavesForTheSameElement(OctaveConnectionError):
    def __str__(self) -> str:
        assert isinstance(self._i, OctaveIfInputPort)
        assert isinstance(self._q, OctaveIfInputPort)
        return (
            f"The I port is connected to {self._i.device_name} and Q is connected to {self._q.device_name}. "
            f"Both of them should be connected to the same Octave, with the same number (i.e. I1 & Q1 etc.)."
        )


class DifferentOctaveInputsForTheSameElement(OctaveConnectionError):
    def __str__(self) -> str:
        assert isinstance(self._i, OctaveIfInputPort)
        assert isinstance(self._q, OctaveIfInputPort)
        return (
            f"The I port is connected to {self._i.port_name.name} and Q is connected to {self._q.port_name.name}. "
            f"Both of them should be connected to the same Octave, with the same number (i.e. I1 & Q1 etc.)."
        )


class BothPortsConnectedToTheSameOctavePort(OctaveConnectionError):
    def __str__(self) -> str:
        assert isinstance(self._i, OctaveIfInputPort)
        return (
            f"Both I and Q port are connected to {(self._i.device_name, self._i.port_name.name)}. "
            f"This is probably a configuration mistake."
        )


class ElementsDB(Dict[str, BasicElement]):
    def __missing__(self, key: str) -> None:
        raise ElementNotFound(key)


INPUTS_TO_ELEMENTS = {
    type(None): BasicElement,
    QuaConfigMixInputs: MixInputsElement,
    QuaConfigSingleInput: SingleInputElement,
    QuaConfigMultipleInputs: MultipleInputsElement,
    QuaConfigSingleInputCollection: SingleInputCollectionElement,
}


def init_elements(
    pb_config: QuaConfig,
    frontend_api: FrontendApi,
    machine_id: str,
    octave_config: Optional[QmOctaveConfig] = None,
) -> ElementsDB:
    elements = {}
    _octave_manager = _OctavesContainer(pb_config, octave_config)
    for name, element_config in pb_config.v1_beta.elements.items():
        _, element_inputs = betterproto.which_one_of(element_config, "element_inputs_one_of")
        try:
            element_class = INPUTS_TO_ELEMENTS[type(element_inputs)]
        except KeyError:
            raise UnknownElementType(f"Element {name} is of unknown type - {type(element_inputs)}.")
        element = element_class(name, element_config, frontend_api, machine_id)
        element = _octave_manager.add_octave(element)

        elements[name] = element
    return ElementsDB(elements)


class _OctavesContainer:
    def __init__(self, pb_config: QuaConfig, octave_config: Optional[QmOctaveConfig] = None):
        self._pb_config = pb_config
        self._octave_config = octave_config or QmOctaveConfig()
        self._octave_clients_cache: Dict[str, Octave] = {}

    def _get_connections_to_octave(self, element_port: QuaConfigDacPortReference) -> MaybeOctaveInputPort:
        controller, number = element_port.controller, element_port.number
        controller_config = self._pb_config.v1_beta.controllers[controller]
        connection = controller_config.analog_outputs[number].octave_connectivity
        if betterproto.serialized_on_wire(connection):
            return connection
        res = self._octave_config.get_octave_input_port(controller, number)
        if res is None:
            return None
        octave_name, port_name = res
        return OctaveIfInputPort(device_name=octave_name, port_name=OctaveIfInputPortName[port_name])

    def _get_loopbacks(self, octave_name: str) -> Dict[OctaveLOSource, OctaveOutput]:
        if octave_name in self._pb_config.v1_beta.octaves:
            pb_loopbacks = self._pb_config.v1_beta.octaves[octave_name].loopbacks
            if pb_loopbacks:
                loopbacks = {}
                for loopback in pb_loopbacks:
                    source_octave = loopback.lo_source_generator.device_name
                    if source_octave != octave_name:
                        raise OctaveLoopbackError("lo loopback between different octave devices are not supported")
                    lo_source_input = OctaveLOSource[loopback.lo_source_input.name]
                    loopbacks[lo_source_input] = OctaveOutput[loopback.lo_source_generator.port_name.name]
                return loopbacks
            else:
                return {}
        return self._octave_config.get_lo_loopbacks_by_octave(octave_name)

    @staticmethod
    def _validate_octave_is_connected_properly(
        i_octave_input_port: MaybeOctaveInputPort, q_octave_input_port: MaybeOctaveInputPort
    ) -> None:
        if i_octave_input_port is None and q_octave_input_port is None:
            return
        if (i_octave_input_port is None) != (q_octave_input_port is None):
            raise OnlyOneConnectedPort(i_octave_input_port, q_octave_input_port)
        assert isinstance(i_octave_input_port, OctaveIfInputPort)
        assert isinstance(q_octave_input_port, OctaveIfInputPort)
        if i_octave_input_port.device_name != q_octave_input_port.device_name:
            raise DifferentOctavesForTheSameElement(i_octave_input_port, q_octave_input_port)
        if i_octave_input_port.port_name.name[-1] != q_octave_input_port.port_name.name[-1]:
            raise DifferentOctaveInputsForTheSameElement(i_octave_input_port, q_octave_input_port)
        if i_octave_input_port == q_octave_input_port:
            raise BothPortsConnectedToTheSameOctavePort(i_octave_input_port, q_octave_input_port)

    def add_octave(self, element: BasicElement) -> BasicElement:
        if not isinstance(element, MixInputsElement):
            return element

        i_octave_input_port = self._get_connections_to_octave(element.i_port)
        q_octave_input_port = self._get_connections_to_octave(element.q_port)

        self._validate_octave_is_connected_properly(i_octave_input_port, q_octave_input_port)
        if i_octave_input_port is None:
            if element.has_octave_params:
                raise ValueError("Element has octave params even though it is not connected to an Octave.")
            return element

        # TODO - add this when we fully move to configuration of the octave in the qua-config
        # if not element.has_octave_params:
        #     raise ValueError("Element does not have octave params even though it is connected to an Octave.")
        client = self._get_octave_client(i_octave_input_port.device_name)
        if betterproto.serialized_on_wire(element._config.mix_inputs.octave_params.rf_input_port):
            downconversion_client_name = element._config.mix_inputs.octave_params.rf_input_port.device_name
            downconversion_client = self._get_octave_client(downconversion_client_name)
            downconversion_port_number = element._config.mix_inputs.octave_params.rf_input_port.port_name.value + 1
        else:
            downconversion_client, downconversion_port_number = None, None
        return ElementWithOctave(
            element._name,
            element._config,
            element._frontend,
            element._id,
            client=client,
            octave_if_input_port_number=int(i_octave_input_port.port_name.name[-1]),
            downconversion_client=downconversion_client,
            octave_rf_input_port_number=downconversion_port_number,
        )

    def _get_octave_client(self, device_name: str) -> Octave:
        if device_name in self._octave_clients_cache:
            return self._octave_clients_cache[device_name]

        device_connection_info = self._octave_config.devices[device_name]
        loopbacks = self._get_loopbacks(device_name)
        client = Octave(
            host=device_connection_info.host,
            port=device_connection_info.port,
            port_mapping=loopbacks,
            octave_name=device_name,
            fan=self._octave_config.fan,
        )
        self._octave_clients_cache[device_name] = client
        return client
