import logging
import warnings
import contextlib
from enum import Enum
from time import perf_counter
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional

from octave_sdk.octave import ClockInfo
from octave_sdk import IFMode, ClockType, RFOutputMode, ClockFrequency, OctaveLOSource, RFInputLOSource, RFInputRFSource

from qm import QuantumMachine
from qm.exceptions import OpenQmException
from qm.api.models.capabilities import ServerCapabilities
from qm.octave._calibration_config import _prep_config, _get_frequencies
from qm.octave.calibration_db import CalibrationResult, octave_output_mixer_name
from qm.octave.octave_config import QmOctaveConfig, _convert_octave_port_to_number

if TYPE_CHECKING:
    from qm.quantum_machines_manager import QuantumMachinesManager

try:
    from octave_sdk import Octave

    OCTAVE_SDK_LOADED = True

except ModuleNotFoundError:
    # Error handling
    OCTAVE_SDK_LOADED = False
    Octave = None

logger = logging.getLogger(__name__)


class OctaveSDKException(Exception):
    pass


class SetFrequencyException(Exception):
    pass


class ClockMode(Enum):
    Internal = (ClockType.Internal, None)
    External_10MHz = (ClockType.External, ClockFrequency.MHZ_10)
    External_100MHz = (ClockType.External, ClockFrequency.MHZ_100)
    External_1000MHz = (ClockType.Buffered, ClockFrequency.MHZ_1000)


def _run_compiled(compiled_id: str, qm: QuantumMachine):
    from qm.octave._calibration_program import _process_results

    pending_job = qm.queue.add_compiled(compiled_id)
    job = pending_job.wait_for_execution()
    all_done = job.result_handles.wait_for_all_values(timeout=30)
    if not all_done:
        _calibration_failed_error()
    res = _get_results(
        [
            "error",
            "i_track",
            "q_track",
            "c00",
            "c01",
            "c10",
            "c11",
        ],
        job,
    )
    # g_track,
    # phi_track,
    # bool_lo_power_small,
    # bool_lo_step_size_small,
    # bool_too_many_iterations,
    # bool_image_power_small,
    # bool_image_step_size_small,
    # final_g = g_track[-1]
    # final_phi = phi_track[-1]
    # import numpy as np
    # lo = lo
    # if lo[-1] == 0:
    #     lo[-1] = 2 ** -28
    # image = image
    # if image[-1] == 0:
    #     image[-1] = 2 ** -28
    # signal = signal
    # if signal[-1] < 0:
    #     signal[-1] = 8 - signal[-1]
    # exit_lo = (
    #     1 * bool_lo_power_small
    #     + 2 * bool_lo_step_size_small
    #     + 4 * bool_too_many_iterations
    # )
    # print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    # print(
    #     f"LO suppression is {10 * np.log10(signal[-1] / lo[-1]):.4f} dBc at (I,"
    #     f"Q) = ({final_i:.4f},{final_q:.4f}) "
    # )
    # print(exit_lo)
    # #
    # exit_image = (
    #     1 * bool_image_power_small
    #     + 2 * bool_image_step_size_small
    #     + 4 * bool_too_many_iterations
    # )
    # print(
    #     f"Image suppression is {10 * np.log10(signal[-1] / image[-1]):.4f} dBc "
    #     f"at (g,phi) = ({final_g:.4f},{final_phi:.4f}) "
    # )
    # print(exit_image)
    # print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    return _process_results(
        res["error"],
        res["i_track"],
        res["q_track"],
        res["c00"],
        res["c01"],
        res["c10"],
        res["c11"],
    )


def _calibration_failed_error(extra: str = None):
    raise Exception(
        f"There was a problem during calibration. please check opx is on"
        f" and valid. If this continues, please contact QM support{extra}"
    )


def _get_results(names, job):
    res = {}
    for name in names:
        if name not in job.result_handles:
            _calibration_failed_error(f"\nerror in result {name}")
        res[name] = job.result_handles.get(name).fetch_all(flat_struct=True)
    return res


def _convert_rf_output_index_to_input_source(rf_output) -> RFInputRFSource:
    if rf_output == 1:
        return RFInputRFSource.Loopback_RF_out_1
    elif rf_output == 2:
        return RFInputRFSource.Loopback_RF_out_2
    elif rf_output == 3:
        return RFInputRFSource.Loopback_RF_out_3
    elif rf_output == 4:
        return RFInputRFSource.Loopback_RF_out_4
    elif rf_output == 5:
        return RFInputRFSource.Loopback_RF_out_5


class OctaveManager:
    def __init__(
        self,
        config: Optional[QmOctaveConfig] = None,
        qmm: Optional["QuantumMachinesManager"] = None,
        capabilities: ServerCapabilities = None,
    ) -> None:

        self._octave_config: QmOctaveConfig
        self._qmm = qmm
        self._capabilities: ServerCapabilities = capabilities

        self._check_and_set_config(config)
        self._initialize()

    def _check_and_set_config(self, config):
        if config and isinstance(config, QmOctaveConfig):
            self._octave_config: QmOctaveConfig = config
        elif config is None:
            self._octave_config: QmOctaveConfig = QmOctaveConfig()
        else:
            raise TypeError("config must be of type QmOctaveConfig")

    def _initialize(self):
        self._octave_clients: Dict[str, Octave] = {}
        devices = self._octave_config.get_devices()

        if devices is not None and len(devices) > 0:
            if not OCTAVE_SDK_LOADED:
                raise OctaveSDKException("Octave sdk is not installed")
            for device_name, connection_info in devices.items():
                loop_backs = self._octave_config.get_lo_loopbacks_by_octave(device_name)
                loop_backs = {input_port: output_port for input_port, output_port in loop_backs.items()}
                self._octave_clients[device_name] = Octave(
                    host=connection_info.host,
                    port=connection_info.port,
                    port_mapping=loop_backs,
                    octave_name=device_name,
                    fan=self._octave_config.fan,
                )

    def set_octave_configuration(self, config: QmOctaveConfig):
        """Args:
        config
        """
        self._check_and_set_config(config)
        self._initialize()

    def get_output_port(
        self,
        opx_i_port: Tuple[str, int],
        opx_q_port: Tuple[str, int],
    ) -> Tuple[str, int]:
        # check both ports are going to the same mixer
        connections = self._octave_config.get_opx_octave_port_mapping()
        i_octave_port = connections[opx_i_port]
        q_octave_port = connections[opx_q_port]
        if i_octave_port[0] != q_octave_port[0]:
            raise Exception("I and Q are not connected to the same octave")
        if i_octave_port[1][-1] != q_octave_port[1][-1]:
            raise Exception("I and Q are not connected to the same octave input")

        return i_octave_port[0], _convert_octave_port_to_number(i_octave_port[1])

    def _get_client(self, octave_port):
        octave = self._octave_clients[octave_port[0]]
        return octave

    def restore_default_state(self, octave_name):
        self._octave_clients[octave_name].restore_default_state()

    def start_batch_mode(self):
        for client in self._octave_clients.values():
            client.start_batch_mode()

    def end_batch_mode(self):
        for client in self._octave_clients.values():
            client.end_batch_mode()

    @contextlib.contextmanager
    def batch_mode(self):

        self.start_batch_mode()
        yield
        self.end_batch_mode()

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
            octave_name: str
            clock_type: ClockType
            frequency: ClockFrequency
            clock_mode: ClockMode

        Returns:

        """
        if clock_mode is None:
            warnings.warn(
                "set_clock is changing its API, and the 'clock_type' and 'frequency' arguments will be "
                "removed in the next version, please use the 'mode' parameter.",
                category=DeprecationWarning,
            )
        else:
            clock_type, frequency = clock_mode.value

        self._octave_clients[octave_name].set_clock(clock_type, frequency)
        self._octave_clients[octave_name].save_default_state(only_clock=True)

    def get_clock(self, octave_name: str) -> ClockInfo:
        """Return the octave clock type and frequency

        Args:
            octave_name: str

        Returns:
            ClockInfo
        """
        clock = self._octave_clients[octave_name].get_clock()
        return ClockInfo(clock.clock_type, clock.frequency)

    def set_lo_frequency(
        self,
        octave_output_port: Tuple[str, int],
        lo_frequency: float,
        lo_source: OctaveLOSource = OctaveLOSource.Internal,
        set_source: bool = True,
    ):
        """Sets the LO frequency of the synthesizer associated to element

        Args:
            octave_output_port
            lo_frequency
            lo_source
            set_source
        """
        octave = self._get_client(octave_output_port)
        octave_name, port_index = octave_output_port

        loop_backs = self._octave_config.get_lo_loopbacks_by_octave(octave_name)

        if lo_source != OctaveLOSource.Internal and lo_source not in loop_backs:
            raise SetFrequencyException(f"Cannot set frequency to an external lo source" f" {lo_source.name}")

        if set_source:
            octave.rf_outputs[port_index].set_lo_source(lo_source)

        octave.rf_outputs[port_index].set_lo_frequency(lo_source, lo_frequency)
        # octave.save_default_state()

    def set_lo_source(self, octave_output_port: Tuple[str, int], lo_port: OctaveLOSource):
        """Sets the source of LO going to the upconverter associated with element.

        Args:
            octave_output_port
            lo_port
        """
        octave = self._get_client(octave_output_port)
        octave.rf_outputs[octave_output_port[1]].set_lo_source(lo_port)
        # octave.save_default_state()

    def set_rf_output_mode(self, octave_output_port: Tuple[str, int], switch_mode: RFOutputMode):
        """Configures the output switch of the upconverter associated to element.
        switch_mode can be either: 'always_on', 'always_off', 'normal' or 'inverted'
        When in 'normal' mode a high trigger will turn the switch on and a low
        trigger will turn it off
        When in 'inverted' mode a high trigger will turn the switch off and a low
        trigger will turn it on
        When in 'always_on' the switch will be permanently on. When in 'always_off'
        mode the switch will be permanently off.

        Args:
            octave_output_port
            switch_mode
        """
        octave = self._get_client(octave_output_port)
        octave.rf_outputs[octave_output_port[1]].set_output(switch_mode)
        # octave.save_default_state()

    def set_rf_output_gain(
        self,
        octave_output_port: Tuple[str, int],
        gain_in_db: float,
        lo_frequency: Optional[float] = None,
    ):
        """Sets the RF output gain for the upconverter associated with element.
        if no lo_frequency is given, and lo source is internal, will use the
        internal frequency

        Args:
            octave_output_port
            gain_in_db
            lo_frequency
        """
        octave = self._get_client(octave_output_port)
        octave.rf_outputs[octave_output_port[1]].set_gain(gain_in_db, lo_frequency)
        # octave.save_default_state()

    def set_downconversion_lo_source(
        self,
        octave_input_port: Tuple[str, int],
        lo_source: RFInputLOSource,
        lo_frequency: Optional[float] = None,
        disable_warning: Optional[bool] = False,
    ):
        """Sets the LO source for the downconverters.

        Args:
            octave_input_port
            lo_source
            lo_frequency
            disable_warning
        """
        octave = self._get_client(octave_input_port)
        octave.rf_inputs[octave_input_port[1]].set_lo_source(lo_source)
        octave.rf_inputs[octave_input_port[1]].set_rf_source(RFInputRFSource.RF_in)
        internal = lo_source == RFInputLOSource.Internal or lo_source == RFInputLOSource.Analyzer
        if lo_frequency is not None and internal:
            octave.rf_inputs[octave_input_port[1]].set_lo_frequency(source_name=lo_source, frequency=lo_frequency)
        # octave.save_default_state()

    def set_downconversion_if_mode(
        self,
        octave_input_port: Tuple[str, int],
        if_mode_i: IFMode = IFMode.direct,
        if_mode_q: IFMode = IFMode.direct,
        disable_warning: Optional[bool] = False,
    ):
        """Sets the IF downconversion stage.
        if_mode can be one of: 'direct', 'mixer', 'envelope_DC', 'envelope_AC','OFF'
        If only one value is given the setting is applied to both IF channels
        (I and Q) for the downconverter associated to element
        (how will we know that? shouldn't this be per downconverter?)
        If if_mode is a tuple, then the IF stage will be assigned to each
        quadrature independently, i.e.:
        if_mode = ('direct', 'envelope_AC') will set the I channel to be
        direct and the Q channel to be 'envelope_AC'

        Args:
            disable_warning
            octave_input_port
            if_mode_q
            if_mode_i
        """

        octave = self._get_client(octave_input_port)
        octave.rf_inputs[octave_input_port[1]].set_if_mode_i(if_mode_i)
        octave.rf_inputs[octave_input_port[1]].set_if_mode_q(if_mode_q)

    def reset(self, octave_name: str) -> bool:
        """
        Will reset the entire Octave HW to default off state
        Warning, will block the code until reset completes

        :param octave_name: str
        :return: True on success, False otherwise
        """
        if self._capabilities.supports_octave_reset:
            return self._octave_clients[octave_name].reset()
        else:
            logger.error("QOP version do not support Octave reset function")
            return False

    def calibrate(
        self,
        octave_output_port: Tuple[str, int],
        lo_if_frequencies_tuple_list: List[Tuple] = None,
        save_to_db=True,
        close_open_quantum_machines=True,
        optimizer_parameters: Optional[dict] = None,
        **kwargs,
    ) -> Dict[Tuple[int, int], CalibrationResult]:
        """calibrates IQ mixer associated with element

        Args:
            close_open_quantum_machines: Boolean, if true (default) all
                running QMs
            octave_output_port
            lo_if_frequencies_tuple_list: A list of LO/IF frequencies
                for which the calibration is to be performed [(LO1,
                IF1), (LO2, IF2), ...]
            save_to_db
            optimizer_parameters
        will be closed for the calibration. Otherwise,
        calibration might fail if there are not enough resources for the calibration
        """
        calibration_start = perf_counter()
        if kwargs:
            logger.warning(f"unused kwargs: {list(kwargs)}, please remove them.")

        octave = self._get_client(octave_output_port)
        output_port = octave_output_port[1]
        calibration_input = 2
        optimizer_parameters = self._get_optimizer_parameters(optimizer_parameters)

        lo_to_if_mapping = create_lo_to_if_list_mapping(lo_if_frequencies_tuple_list)
        if len(lo_to_if_mapping) > 1:  # TODO fix loop bug and remove this error, from here the code assumes 1 lo_freq
            raise NotImplementedError("Multiple lo frequencies is not yet supported.")

        lo_freq, if_freq_list = lo_to_if_mapping.popitem()

        first_if = if_freq_list[0]
        t_end_preparation = perf_counter()
        logger.debug(f"Pre calibration preparation took {t_end_preparation - calibration_start}")
        compiled, qm = self._compile_calibration_program(
            lo_freq,
            first_if,
            octave_output_port,
            optimizer_parameters,
            close_open_quantum_machines,
        )
        t_start_setup = perf_counter()

        state_name_before = self._set_octave_for_calibration(
            octave,
            calibration_input,
            output_port,
            skewed_lo_freq=lo_freq + optimizer_parameters["calibration_offset_frequency"],
        )
        t_end_setup = perf_counter()
        logger.debug(f"Setting octave for LO took {t_end_setup - t_start_setup}.")

        result = {}
        for if_freq in if_freq_list:
            t_start_setup = perf_counter()
            self._set_if_freq(qm, if_freq, optimizer_parameters)
            t_end_setup = perf_counter()
            logger.debug(f"Setting octave for IF took {t_end_setup - t_start_setup}.")

            dc_offsets, correction = _run_compiled(compiled, qm)
            t_end_run = perf_counter()
            logger.debug(f"Running QUA calibration took {t_end_setup - t_end_run}.")
            temp = octave.rf_outputs[output_port].get_temperature()

            result[lo_freq, if_freq] = CalibrationResult(
                mixer_id=octave_output_mixer_name(*octave_output_port),
                correction=correction,
                i_offset=dc_offsets[0],
                q_offset=dc_offsets[1],
                temperature=temp,
                if_frequency=if_freq,
                lo_frequency=lo_freq,
                optimizer_parameters=optimizer_parameters,
            )

            if save_to_db and self._octave_config.calibration_db is not None:
                self._octave_config.calibration_db.update_calibration_data(result[lo_freq, if_freq])

        # set to previous state
        t_start_restoration = perf_counter()
        octave.restore_state(state_name_before)
        # Close the qm
        qm.close()
        t_end = perf_counter()
        logger.debug(f"Restoring setup and closing QM took QUA calibration took {t_end - t_start_restoration}.")
        logger.debug(f"Calibration took {t_end - calibration_start}.")
        return result

    def _get_optimizer_parameters(self, optimizer_parameters):
        optimizer_parameters_defaults = {
            "average_iterations": 100,
            "iterations": 10000,
            "calibration_offset_frequency": 7e6,
            "keep_on": False,
        }
        if optimizer_parameters is not None:
            for p in optimizer_parameters:
                if p in optimizer_parameters_defaults:
                    optimizer_parameters_defaults[p] = optimizer_parameters[p]
                else:
                    raise ValueError(f"optimizer parameter {p} is not supported")
        return optimizer_parameters_defaults

    def _compile_calibration_program(
        self,
        first_lo,
        first_if,
        octave_output_port,
        optimizer_parameters,
        close_open_quantum_machines=True,
    ):
        from qm.octave._calibration_program import _generate_program

        iq_channels = self._octave_config.get_opx_iq_ports(octave_output_port)
        controller_name = iq_channels[0][0]
        adc_channels = [(controller_name, 1), (controller_name, 2)]
        config = _prep_config(
            iq_channels,
            adc_channels,
            first_if,
            first_lo,
            optimizer_parameters,
        )
        prog = _generate_program(optimizer_parameters)
        try:
            t0 = perf_counter()
            qm = self._qmm.open_qm(config, close_other_machines=close_open_quantum_machines)
            logger.debug(f"Creating dedicated QM for calibration took {perf_counter() - t0}")
        except OpenQmException as e:
            raise OpenQmException("Mixer calibration failed: Could not open a quantum machine.") from e

        t0 = perf_counter()
        compiled = qm.compile(prog)
        logger.debug(f"Compiling calibration program took {perf_counter() - t0}.")

        return compiled, qm

    @staticmethod
    def _set_if_freq(qm, if_freq, optimizer_parameters):
        down_mixer_offset, signal_freq, image_freq = _get_frequencies(if_freq, optimizer_parameters)
        with qm.octave.batch_mode():
            qm.set_intermediate_frequency("IQmixer", if_freq)
            qm.set_intermediate_frequency("signal_analyzer", signal_freq)
            qm.set_intermediate_frequency("lo_analyzer", down_mixer_offset)
            qm.set_intermediate_frequency("image_analyzer", image_freq)

    @staticmethod
    def _set_octave_for_calibration(octave, calibration_input, output_port, skewed_lo_freq) -> str:
        octave.start_batch_mode()
        state_name_before = "before_cal"
        octave.snapshot_state(state_name_before)
        # switch to loopback mode to listen in on the RF output
        octave.rf_inputs[calibration_input].set_rf_source(_convert_rf_output_index_to_input_source(output_port))
        octave.rf_inputs[calibration_input].set_if_mode_i(IFMode.direct)
        octave.rf_inputs[calibration_input].set_if_mode_q(IFMode.direct)
        octave.rf_inputs[1].set_if_mode_i(IFMode.off)
        octave.rf_inputs[1].set_if_mode_q(IFMode.off)
        octave.rf_outputs[output_port].set_output(RFOutputMode.on)

        octave.rf_inputs[calibration_input].set_lo_source(RFInputLOSource.Analyzer)

        octave.rf_inputs[calibration_input].set_lo_frequency(RFInputLOSource.Analyzer, skewed_lo_freq)
        octave.end_batch_mode()
        return state_name_before


def create_lo_to_if_list_mapping(lo_if_frequencies_tuple_list: List[Tuple[int, int]]) -> Dict[int, List[int]]:
    lo_to_if_mapping = defaultdict(list)
    for lo_freq, if_freq in lo_if_frequencies_tuple_list:
        lo_to_if_mapping[lo_freq].append(if_freq)
    return lo_to_if_mapping
