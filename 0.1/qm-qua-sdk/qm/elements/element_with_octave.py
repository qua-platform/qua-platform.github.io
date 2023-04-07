from typing import Optional

import betterproto
from octave_sdk.octave import Octave, ClockInfo  # type: ignore[import]
from octave_sdk import (  # type: ignore[import]
    IFMode,
    ClockType,
    RFOutputMode,
    ClockFrequency,
    OctaveLOSource,
    RFInputLOSource,
    RFInputRFSource,
)

from qm.api.frontend_api import FrontendApi
from qm.grpc.octave_models import OctaveLoSourceInput
from qm.elements.native_elements import MixInputsElement
from qm.grpc.qua_config import QuaConfigElementDec, QuaConfigOutputSwitchState


class NoOctaveSdkException(Exception):
    pass


class SetFrequencyException(Exception):
    pass


class ElementWithOctave(MixInputsElement):
    def __init__(
        self,
        name: str,
        config: QuaConfigElementDec,
        frontend_api: FrontendApi,
        machine_id: str,
        client: Octave,
        octave_if_input_port_number: int,
        downconversion_client: Optional[Octave],
        octave_rf_input_port_number: Optional[int],
    ):
        super().__init__(name, config, frontend_api, machine_id)
        self._client = client
        self._octave_if_input_port_number_backup = octave_if_input_port_number
        self._downconversion_client = downconversion_client
        self._octave_rf_input_port_number = octave_rf_input_port_number

    def set_client(self) -> None:
        """
        This function is intended to be used from outside, using the batch mode,
        to run it in parallel on all the quantum-elements, on all the octaves
        """
        octave_params = self._config.mix_inputs.octave_params
        if octave_params.lo_source:
            self.set_lo_source(OctaveLOSource[octave_params.lo_source.name])
        else:
            self.set_lo_source(OctaveLOSource.Internal)

        if self.lo_source == OctaveLOSource.Internal and self.lo_source in self._client._port_mapping:
            self.set_lo_frequency(self.lo_frequency, set_source=False)

        if octave_params.output_switch_state != QuaConfigOutputSwitchState.unset:
            output_mode = {
                QuaConfigOutputSwitchState.always_on: RFOutputMode.on,
                QuaConfigOutputSwitchState.always_off: RFOutputMode.off,
                QuaConfigOutputSwitchState.triggered: RFOutputMode.trig_normal,
                QuaConfigOutputSwitchState.triggered_reversed: RFOutputMode.trig_inverse,
            }[octave_params.output_switch_state]
            self.set_rf_output_mode(output_mode)

        if octave_params.output_gain is not None:
            self.set_rf_output_gain(octave_params.output_gain)

        if octave_params.downconversion_lo_source not in {OctaveLoSourceInput.Off, 0}:
            self._set_downconversion_lo(
                lo_source=RFInputLOSource[octave_params.downconversion_lo_source.name],
                lo_frequency=octave_params.downconversion_lo_frequency or None,
            )

    def set_downconversion_port(self, downconversion_client: Octave, octave_rf_input_port_number: int) -> None:
        self._downconversion_client = downconversion_client
        self._octave_rf_input_port_number = octave_rf_input_port_number

    @property
    def _octave_if_input_port_number(self) -> int:
        if betterproto.serialized_on_wire(self._config.mix_inputs.octave_params):
            enum_number = self._config.mix_inputs.octave_params.rf_output_port.port_name.value + 1
            # The enums are 0-based and the ports are 1-based
        else:
            enum_number = self._octave_if_input_port_number_backup
        return enum_number

    @property
    def lo_source(self) -> OctaveLOSource:
        return self._client.rf_outputs[self._octave_if_input_port_number].get_lo_source()

    def set_lo_frequency(self, lo_frequency: float, set_source: bool = True) -> None:
        # TODO - validate that LO frequency can be casted to int, or it should be a float in the proto
        """
        Sets the LO frequency of the synthesizer associated to element

        :param lo_frequency:
        :param set_source:
        """
        if self.lo_source != OctaveLOSource.Internal and self.lo_source not in self._client._port_mapping:
            raise SetFrequencyException(f"Cannot set frequency to an external lo source {self.lo_source.name}")

        if set_source:
            self._client.rf_outputs[self._octave_if_input_port_number].set_lo_source(
                self.lo_source, ignore_shared_errors=True
            )

        self._client.rf_outputs[self._octave_if_input_port_number].set_lo_frequency(self.lo_source, lo_frequency)
        self.lo_frequency = lo_frequency

    def set_lo_source(self, lo_port: OctaveLOSource) -> None:
        """
        Sets the source of LO going to the upconverter associated with element.
        :param lo_port:
        """
        self._client.rf_outputs[self._octave_if_input_port_number].set_lo_source(lo_port, ignore_shared_errors=True)

    def set_rf_output_mode(self, switch_mode: RFOutputMode) -> None:
        """
        Configures the output switch of the upconverter associated to element.
        switch_mode can be either: 'always_on', 'always_off', 'normal' or 'inverted'
        When in 'normal' mode a high trigger will turn the switch on and a low trigger will turn it off
        When in 'inverted' mode a high trigger will turn the switch off and a low trigger will turn it on
        When in 'always_on' the switch will be permanently on. When in 'always_off' mode the switch will
        be permanently off.

        :param switch_mode:
        """
        self._client.rf_outputs[self._octave_if_input_port_number].set_output(switch_mode)

    def set_rf_output_gain(self, gain_in_db: float) -> None:
        """
        Sets the RF output gain for the up-converter associated with the element.
        RF_gain is in steps of 0.5dB from -20 to +24 and is referring
        to the maximum OPX output power of 4dBm (=0.5V pk-pk) So for a value of -24
        for example, an IF signal coming from the OPX at max power (4dBm) will be
        upconverted and come out of Octave at -20dBm

        :param gain_in_db:
        """
        # a. use value custom set in qm.octave.update_external
        # b. use value from config
        self._client.rf_outputs[self._octave_if_input_port_number].set_gain(gain_in_db, self.lo_frequency)

    def set_downconversion(
        self,
        lo_source: Optional[RFInputLOSource] = None,
        lo_frequency: Optional[float] = None,
        if_mode_i: IFMode = IFMode.direct,
        if_mode_q: IFMode = IFMode.direct,
    ) -> None:
        """
        Sets the LO source for the downconverters.
        The LO source will be the one associated with the upconversion of element

        :param lo_source:
        :param lo_frequency:
        :param if_mode_i:
        :param if_mode_q:
        """
        self._set_downconversion_lo(lo_source, lo_frequency)
        self._set_downconversion_if_mode(if_mode_i, if_mode_q)

    def _set_downconversion_lo(
        self,
        lo_source: Optional[RFInputLOSource] = None,
        lo_frequency: Optional[float] = None,
    ) -> None:
        """
        Sets the LO source for the downconverters.
        If no value is given the LO source will be the one associated with the
        upconversion of element

        :param lo_frequency:
        :param lo_source:
        """
        # TODO check if the downconversion shared between elements(from same rf_in or both rf_ins)
        # if we have two elements for the same downconversion:
        # warning when setting for port that has multiple elements
        # “element x shares the input port with elements [y],
        # any settings applied will affect all elements”
        if self._octave_rf_input_port_number is None:
            raise AttributeError("This element has no connection ot octave RF-in, cannot set downconversion")

        if lo_source is None:
            lo_source = self.lo_source

        if self._downconversion_client:
            self._downconversion_client.rf_inputs[self._octave_rf_input_port_number].set_lo_source(
                lo_source, ignore_shared_errors=True
            )
            self._downconversion_client.rf_inputs[self._octave_rf_input_port_number].set_rf_source(
                RFInputRFSource.RF_in
            )
            is_internal = lo_source in {RFInputLOSource.Internal, RFInputLOSource.Analyzer}

            if lo_frequency is not None and is_internal:
                self._downconversion_client.rf_inputs[self._octave_rf_input_port_number].set_lo_frequency(
                    source_name=lo_source, frequency=lo_frequency
                )

    def _set_downconversion_if_mode(self, if_mode_i: IFMode = IFMode.direct, if_mode_q: IFMode = IFMode.direct) -> None:
        if self._octave_rf_input_port_number is None:
            raise AttributeError("This element has no connection ot octave RF-in, cannot set downconversion")
        if self._downconversion_client:
            self._downconversion_client.rf_inputs[self._octave_rf_input_port_number].set_if_mode_i(if_mode_i)
            self._downconversion_client.rf_inputs[self._octave_rf_input_port_number].set_if_mode_q(if_mode_q)

    def set_clock(self, clock_type: ClockType, frequency: Optional[ClockFrequency]) -> None:
        """
        This function will set the octave clock type - internal, external or buffered.
        It can also set the clock frequency - 10, 100 or 1000 MHz

        :param clock_type: ClockType
        :param frequency: ClockFrequency
        """
        self._client.set_clock(clock_type, frequency)
        self._client.save_default_state(only_clock=True)

    @property
    def clock(self) -> ClockInfo:
        return self._client.get_clock()
