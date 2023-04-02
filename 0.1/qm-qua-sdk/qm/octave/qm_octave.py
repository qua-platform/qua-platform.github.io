import warnings
from typing import Dict, List, Tuple, Union, Optional, ContextManager

from octave_sdk.octave import ClockInfo
from octave_sdk import IFMode, ClockType, RFOutputMode, ClockFrequency, OctaveLOSource, RFInputLOSource

from qm.elements_db import ElementsDB
from qm.octave.calibration_db import CalibrationResult
from qm.elements.element_with_octave import ElementWithOctave
from qm.octave.octave_manager import ClockMode, OctaveManager


class ElementHasNoOctaveError(Exception):
    pass


class QmOctave:
    def __init__(self, elements_db: ElementsDB, octave_manager) -> None:
        super().__init__()
        self._elements_db = elements_db
        self._octave_manager: OctaveManager = octave_manager

    def start_batch_mode(self):
        self._octave_manager.start_batch_mode()

    def end_batch_mode(self):
        self._octave_manager.end_batch_mode()

    def batch_mode(self) -> ContextManager:
        return self._octave_manager.batch_mode()

    def set_qua_element_octave_rf_in_port(self, element, octave_name, rf_input_index):
        """Sets the octave downconversion port for the element.

        Args:
            element (str): The name of the element
            octave_name (str): The octave name
            rf_input_index (RFInputRFSource): input index
        """
        inst = self._elements_db[element]
        client = self._octave_manager._octave_clients[octave_name]
        inst.set_downconversion_port(client, rf_input_index)

    def load_lo_frequency_from_config(self, elements: Union[List, str]):
        """Loads into the octave synthesizers the LO frequencies specified for elements
        in the element list

        Args:
            elements: A list of elements to load LO frequencies from
        """
        warnings.warn(
            "lo_frequency is now set directly from config when a QuantumMachine is created, no need to do it directly. "
            "If you want, you can run over the elements and do set_frequency.",
            category=DeprecationWarning,
        )

    def set_lo_frequency(self, element: str, lo_frequency: float, set_source: bool = True):
        """Sets the LO frequency of the synthesizer associated to element. Will not change the synthesizer if set_source = False

        Args:
            element (str): The name of the element
            lo_frequency (float): The LO frequency
            set_source (Boolean): Set the synthesizer (True) or just
                update the client (False)
        """
        inst = self._elements_db[element]
        inst.set_lo_frequency(lo_frequency, set_source)

    def update_external_lo_frequency(
        self,
        element: str,
        lo_frequency: float,
    ):
        """Updates the client on the external LO frequency (provided by the user)
        associated with element

        Args:
            element (str): The name of the element
            lo_frequency (float): The LO frequency
        """
        self._elements_db[element].lo_frequency = lo_frequency
        self._elements_db[element].set_lo_frequency(lo_frequency)

    def set_lo_source(self, element: str, lo_port: OctaveLOSource):
        """Associate  the given LO source with the given element. Always be sure the given LO source is internally connected to the element

        Args:
            element (str): The name of the element
            lo_port (OctaveLOSource): One of the allowed sources
                according the internal connectivity
        """
        inst = self._elements_db[element]
        if not isinstance(inst, ElementWithOctave):
            raise ElementHasNoOctaveError(f"Element {element} has no octave connected to it.")
        inst.set_lo_source(lo_port)

    def set_rf_output_mode(self, element: str, switch_mode: RFOutputMode):
        """Configures the output switch of the upconverter associated to element.
        switch_mode can be either: 'on', 'off', 'trig_normal' or 'trig_inverse'
        When in 'trig_normal' mode a high trigger will turn the switch on and a low trigger will turn it off
        When in 'trig_inverse' mode a high trigger will turn the switch off and a low trigger will turn it on
        When in 'on' the switch will be permanently on. When in 'off' mode the switch will be permanently off.

        Args:
            element (str): The name of the element
            switch_mode (RFOutputMode): switch mode according to the
                allowed states
        """
        inst = self._elements_db[element]
        inst.set_rf_output_mode(switch_mode)

    def set_rf_output_gain(self, element: str, gain_in_db: float):
        """Sets the RF output gain for the up-converter associated with the element.
        RF_gain is in steps of 0.5dB from -20 to +24 and is referring
        to the maximum OPX output power of 4dBm (=0.5V pk-pk) So for a value of -24
        for example, an IF signal coming from the OPX at max power (4dBm) will be
        upconverted and come out of Octave at -20dBm

        Args:
            element (str): The name of the element
            gain_in_db (float): The RF output gain in dB
        """
        # a. use value custom set in qm.octave.update_external
        # b. use value from config
        inst = self._elements_db[element]
        inst.set_rf_output_gain(gain_in_db)

    def set_downconversion(
        self,
        element: str,
        lo_source: Optional[RFInputLOSource] = None,
        lo_frequency: Optional[float] = None,
        if_mode_i: IFMode = IFMode.direct,
        if_mode_q: IFMode = IFMode.direct,
        disable_warning: bool = False,
    ):
        """Sets the LO source and frequency for the downconverters.
        The LO source will be the one associated with the element's upconversion.
        If only the element is given, the LO source for downconversion will be the upconversion LO of the element.

        Args:
            element (str): The name of the element
            lo_source (RFInputLOSource): allowed LO source
            lo_frequency (float): The LO frequency
            disable_warning (Boolean): Disable warnings about non-
                matching LO sources and elements if True
        """
        inst = self._elements_db[element]
        inst.set_downconversion(lo_source, lo_frequency, if_mode_i, if_mode_q)

    def calibrate_element(
        self,
        element: str,
        lo_if_frequencies_tuple_list: Optional[List[Tuple]] = None,
        save_to_db=True,
        close_open_quantum_machines=True,
        **kwargs,
    ) -> Dict[Tuple[int, int], CalibrationResult]:
        """Calibrate the mixer associated with an element for the given LO & IF frequencies.

        Args:
            close_open_quantum_machines (bool): If true (default) all
                running QMs will be closed for the calibration.
                Otherwise, calibration might fail if there are not
                enough resources for the calibration
            element (str): The name of the element for calibration
            lo_if_frequencies_tuple_list (list): a list of tuples that
                consists of all the (LO,IF) pairs for calibration
            save_to_db (boolean): If true (default), The calibration
                parameters will be saved to the calibration database
        """
        inst = self._elements_db[element]
        octave_port = (inst._client._client._octave_name, inst._octave_if_input_port_number)

        # get IF and LO frequencies from element
        if lo_if_frequencies_tuple_list is None:
            if_frequency = inst.intermediate_frequency
            lo_frequency = inst.lo_frequency
            lo_if_frequencies_tuple_list = [(if_frequency, lo_frequency)]

        return self._octave_manager.calibrate(
            octave_port,
            lo_if_frequencies_tuple_list,
            save_to_db,
            close_open_quantum_machines,
            **kwargs,
        )

    def set_clock(
        self,
        octave_name: str,
        clock_type: Optional[ClockType] = None,
        frequency: Optional[ClockFrequency] = None,
        clock_mode: Optional[ClockMode] = None,
    ):
        """This function will set the octave clock type - internal, external or buffered.
        It can also set the clock frequency - 10, 100 or 1000 MHz

        Args:
            octave_name (str): The octave name to set clock for
            clock_type (ClockType): clock type according to ClockType
            frequency (ClockFrequency): Clock frequency according to ClockFrequency
            clock_mode (ClockMode):
        """
        # TODO: get name from the QMOctave instance
        self._octave_manager.set_clock(octave_name, clock_type, frequency, clock_mode)

    def get_clock(self, octave_name: str) -> ClockInfo:
        """Gets the clock info for a given octave name

        Args:
            octave_name (str): The octave name to get clock for
        :returns ClockInfo: Info about the clock as an object
        """
        return self._octave_manager.get_clock(octave_name)
