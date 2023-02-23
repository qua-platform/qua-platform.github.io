import json
import logging
from typing import Optional, Union, List, Tuple, Dict, TYPE_CHECKING

import numpy
from deprecation import deprecated

from qm.jobs.qm_job import QmJob
from qm.jobs.job_queue import QmQueue
from qm._QmJobErrors import (
    InvalidDigitalInputPolarityError,
)
from qm.api.frontend_api import FrontendApi
from qm.api.job_manager_api import JobManagerApi
from qm.api.models.capabilities import ServerCapabilities
from qm.api.models.compiler import CompilerOptionArguments
from qm.api.models.devices import MixerInfo, AnalogOutputPortFilter, Polarity
from qm.api.simulation_api import SimulationApi
from qm.exceptions import (
    JobCancelledError,
    InvalidConfigError,
    UnsupportedCapabilityError,
)
from qm.grpc.general_messages import Matrix
from qm.jobs.pending_job import QmPendingJob
from qm.jobs.simulated_job import SimulatedJob
from qm.octave import OctaveManager
from qm.octave.qm_octave import QmOctave
from qm.persistence import BaseStore
from qm.program import Program
from qm.program.ConfigBuilder import convert_msg_to_config
from qm.simulate.interface import SimulationConfig
from qm.utils import fix_object_data_type as _fix_object_data_type

if TYPE_CHECKING:
    from qm.grpc.qua_config import QuaConfig

logger = logging.getLogger(__name__)


class QuantumMachine:
    def __init__(
        self,
        machine_id: str,
        pb_config: "QuaConfig",
        frontend_api: FrontendApi,
        capabilities: ServerCapabilities,
        store: BaseStore,
        octave_manager: OctaveManager,
    ):
        self._id = machine_id
        self._config = pb_config
        self._frontend = frontend_api
        self._simulation_api = SimulationApi.from_api(self._frontend)
        self._job_manager = JobManagerApi.from_api(frontend_api)
        self._capabilities = capabilities
        self._store = store
        self._queue = QmQueue(
            config=self._config,
            quantum_machine_id=self._id,
            frontend_api=self._frontend,
            capabilities=self._capabilities,
            store=self._store,
        )
        self._octave = QmOctave(self, octave_manager)

    @deprecated("1.1", "1.2", details="QuantumMachine no longer has 'manager' property")
    @property
    def manager(self):
        """Returns the Quantum Machines Manager"""
        return None

    @property
    def id(self) -> str:
        return self._id

    @property
    def queue(self) -> QmQueue:
        """Returns the queue for the Quantum Machine"""
        return self._queue

    @property
    def octave(self) -> QmOctave:
        return self._octave

    def close(self) -> bool:
        """Closes the quantum machine.

        Returns:
            ``True`` if the close request succeeded, raises an exception
            otherwise.
        """
        return self._frontend.close_quantum_machine(self._id)

    def simulate(
        self,
        program,
        simulate: SimulationConfig,
        compiler_options: Optional[CompilerOptionArguments] = None,
    ):
        """Simulate the outputs of a deterministic QUA program.

        Equivalent to ``execute()`` with ``simulate=SimulationConfig`` (see example).

        Note:
            A simulated job does not support calling QuantumMachine API functions.

        The following example shows a simple execution of the simulator, where the
        associated config object is omitted for brevity.

        Example:
            ```python
            from qm.QuantumMachinesManager import QuantumMachinesManager
            from qm.qua import *
            from qm.simulate import SimulationConfig

            qmManager = QuantumMachinesManager()
            qm1 = qmManager.open_qm(config)

            with program() as prog:
                play('pulse1', 'element1')

            job = qm1.simulate(prog, SimulationConfig(duration=100))
            ```

        Args:
            program: A QUA ``program()`` object to execute
            simulate: A ``SimulationConfig`` configuration object
            kwargs: additional parameteres to pass to execute

        Returns:
            a ``QmJob`` object (see QM Job API).
        """
        job = self.execute(
            program, simulate=simulate, compiler_options=compiler_options
        )
        return job

    def execute(
        self,
        program: Program,
        duration_limit: int = 1000,
        data_limit: int = 20000,
        force_execution: int = False,
        dry_run: int = False,
        simulate: Optional[SimulationConfig] = None,
        compiler_options: Optional[CompilerOptionArguments] = None,
    ) -> QmJob:
        """Executes a program and returns an job object to keep track of execution and get
        results.

        Note:

            Calling execute will halt any currently running program and clear the current
            queue. If you want to add a job to the queue, use qm.queue.add()

        Args:
            program: A QUA ``program()`` object to execute
            duration_limit (int): This parameter is ignored as it is
                obsolete
            data_limit (int): This parameter is ignored as it is
                obsolete
            force_execution (bool): This parameter is ignored as it is
                obsolete
            dry_run (bool): This parameter is ignored as it is obsolete

        Returns:
            A ``QmJob`` object (see QM Job API).
        """
        if type(program) is not Program:
            raise Exception("program argument must be of type qm.program.Program")
        if (
            program.metadata.uses_command_timestamps
            and not self._capabilities.supports_command_timestamps
        ):
            raise UnsupportedCapabilityError(
                "timestamping commands is supported from QOP 2.2 or above"
            )

        if compiler_options is None:
            compiler_options = CompilerOptionArguments()

        if simulate is not None:
            job_id, simulated_response_part = self._simulation_api.simulate(
                self.get_config(), program, simulate, compiler_options
            )
            return SimulatedJob(
                job_id=job_id,
                frontend_api=self._frontend,
                capabilities=self._capabilities,
                store=self._store,
                simulated_response=simulated_response_part,
            )

        self._queue.clear()
        current_running_job = self.get_running_job()
        if current_running_job is not None:
            current_running_job.halt()

        pending_job = self._queue.add(program, compiler_options)
        logger.info("Executing program")
        return pending_job.wait_for_execution(timeout=5)

    def compile(
        self,
        program: Program,
        compiler_options: Optional[CompilerOptionArguments] = None,
    ) -> str:
        """Compiles a QUA program to be executed later. The returned `program_id`
        can then be directly added to the queue. For a detailed explanation
        see [Precompile Jobs](../../Guides/features/#precompile-jobs).

        Args:
            program: A QUA program
            compiler_options: Optional arguments for compilation

        Returns:
            a program_id str

        Example:
            ```python
            program_id = qm.compile(program)
            pending_job = qm.queue.add_compiled(program_id)
            job = pending_job.wait_for_execution()
            ```
        """
        if (
            program.metadata.uses_command_timestamps
            and not self._capabilities.supports_command_timestamps
        ):
            raise UnsupportedCapabilityError(
                "timestamping commands is supported from QOP 2.2 or above"
            )

        logger.info("Compiling program")
        if compiler_options is None:
            compiler_options = CompilerOptionArguments()

        return self._frontend.compile(
            self._id, program.build(self._config), compiler_options
        )

    def list_controllers(self):
        """Gets a list with the defined controllers in this qm

        Returns:
            The names of the controllers configured in this qm
        """
        return tuple(self.get_config()["controllers"].keys())

    def set_mixer_correction(
        self,
        mixer: str,
        intermediate_frequency: Union[int, float],
        lo_frequency: Union[int, float],
        values: Tuple[float, float, float, float],
    ):
        """Sets the correction matrix for correcting gain and phase imbalances
        of an IQ mixer for the supplied intermediate frequency and LO frequency.

        Args:
            mixer (str): the name of the mixer, as defined in the
                configuration
            intermediate_frequency (Union[int|float]): the intermediate
                frequency for which to apply the correction matrix
            lo_frequency (int): the LO frequency for which to apply the
                correction matrix
            values (tuple):

                tuple is of the form (v00, v01, v10, v11) where
                the matrix is
                | v00 v01 |
                | v10 v11 |

        Note:

            Currently, the OPX does not support multiple mixer calibration entries.
            This function will accept IF & LO frequencies written in the config file,
            and will update the correction matrix for all of the elements with the given
            mixer/frequencies combination when the program started.

            It’s not recommended to use this method while a job is running.
            To change the calibration values for a running job,
            use job.set_element_correction
        """
        if (type(values) is not tuple and type(values) is not list) or len(values) != 4:
            raise Exception("correction values must be a tuple of 4 items")

        correction_matrix = Matrix(*[_fix_object_data_type(x) for x in values])

        if self._capabilities.supports_double_frequency:
            frequencies = {
                "lo_frequency_double": float(lo_frequency),
                "intermediate_frequency_double": abs(float(intermediate_frequency)),
            }
        else:
            frequencies = {
                "lo_frequency": int(lo_frequency),
                "intermediate_frequency": abs(int(intermediate_frequency)),
            }

        mixer_info = MixerInfo(
            mixer=mixer, frequency_negative=intermediate_frequency < 0, **frequencies
        )
        self._frontend.set_correction(self._id, mixer_info, correction_matrix)

    def set_intermediate_frequency(self, element: str, freq: float):
        """Sets the intermediate frequency of the element

        Args:
            element (str): the name of the element whose intermediate
                frequency will be updated
            freq (float): the intermediate frequency to set to the given
                element
        """

        logger.debug(
            "Setting element '%s' intermediate frequency to '%s'", element, freq
        )
        if type(element) is not str:
            raise TypeError("element must be a string")
        if not isinstance(freq, (numpy.floating, float)):
            raise TypeError("freq must be a float")

        freq = _fix_object_data_type(freq)

        self._frontend.set_intermediate_frequency(self._id, element, freq)

    def get_output_dc_offset_by_element(self, element: str, input):
        """Get the current DC offset of the OPX analog output channel associated with a element.

        Args:
            element: the name of the element to get the correction for
            input: the port name as appears in the element config.
                Options:

                `'single'`
                    for an element with a single input

                `'I'` or `'Q'`
                    for an element with mixer inputs

        Returns:
            the offset, in normalized output units
        """
        config = self.get_config()

        if element in config["elements"]:
            element_obj = config["elements"][element]
        else:
            raise InvalidConfigError(f"Element {element} not found")

        if "singleInput" in element_obj:
            port = element_obj["singleInput"]["port"]
        elif "mixInputs" in element_obj:
            port = element_obj["mixInputs"][input]
        else:
            raise InvalidConfigError(f"Port {input}, not found")

        if len(port) == 2:
            controller, analog_output = port
        else:
            raise InvalidConfigError(
                "Port format does not recognized. (Use port[0] for the controller and port[1] for the analog output)"
            )

        if controller in config["controllers"]:
            controller = config["controllers"][port[0]]
        else:
            raise InvalidConfigError("Controller does not exist")

        if analog_output in controller["analog_outputs"]:
            return controller["analog_outputs"][port[1]]["offset"]
        else:
            raise InvalidConfigError(f"Controller {controller} does not exist")

    def set_output_dc_offset_by_element(self, element, input, offset):
        """Set the current DC offset of the OPX analog output channel associated with a element.

        Args:
            element (str): the name of the element to update the
                correction for
            input (Union[str, Tuple[str,str], List[str]]): the input
                name as appears in the element config. Options:

                `'single'`
                    for an element with a single input

                `'I'` or `'Q'` or a tuple ('I', 'Q')
                    for an element with mixer inputs
            offset (Union[float, Tuple[float,float], List[float]]): The
                dc value to set to, in normalized output units. Ranges
                from -0.5 to 0.5 - 2^-16 in steps of 2^-16.

        Examples:
            ```python
            qm.set_output_dc_offset_by_element('flux', 'single', 0.1)
            qm.set_output_dc_offset_by_element('qubit', 'I', -0.01)
            qm.set_output_dc_offset_by_element('qubit', ('I', 'Q'), (-0.01, 0.05))
            ```

        Note:

            If the sum of the DC offset and the largest waveform data-point exceed the normalized unit range specified
            above, DAC output overflow will occur and the output will be corrupted.
        """
        logger.debug(
            "Setting DC offset of input '%s' on element '%s' to '%s'",
            input,
            element,
            offset,
        )
        if type(element) is not str:
            raise TypeError("element must be a string")

        if isinstance(input, (tuple, list)):
            if not isinstance(offset, (tuple, list)) or not len(input) == len(offset):
                raise TypeError("input and offset are not of the same length")
            for i, o in zip(input, offset):
                self.set_output_dc_offset_by_element(element, i, o)
            return

        if type(input) is not str:
            raise TypeError("input must be a string or a tuple of strings")
        if offset == 0:
            offset = float(offset)
        if not isinstance(offset, (numpy.floating, float)):
            raise TypeError("offset must be a float or a tuple of floats")

        offset = _fix_object_data_type(offset)

        self._frontend.set_output_dc_offset(self._id, element, input, offset)

    def set_output_filter_by_element(
        self,
        element: str,
        input: str,
        feedforward: Union[List, numpy.ndarray, None],
        feedback: Union[List, numpy.ndarray, None],
    ):
        """Sets the intermediate frequency of the element

        Args:
            element: the name of the element whose ports filters will be
                updated
            input: the input name as appears in the element config.
                Options:

                `'single'`
                    for an element with single input

                `'I'` or `'Q'`
                    for an element with mixer inputs
            feedforward: the values for the feedforward filter
            feedback: the values for the feedback filter

        """
        logger.debug(
            f"Setting output filter of port '{input}' on element '{element}' "
            + f"to (feedforward: {feedforward}, feedback: {feedback})"
        )
        if type(element) is not str:
            raise TypeError("element must be a string")
        if type(input) is not str:
            raise TypeError("port must be a string")
        if feedforward is not None and not isinstance(
            feedforward, (numpy.ndarray, List)
        ):
            raise TypeError("feedforward must be a list or None")

        if feedback is not None and not isinstance(feedback, (numpy.ndarray, List)):
            raise TypeError("feedback must be a list or None")

        self._frontend.set_output_filter_taps(
            self._id,
            element,
            input,
            AnalogOutputPortFilter(feedforward=feedforward, feedback=feedback),
        )

    def set_input_dc_offset_by_element(self, element, output, offset):
        """set the current DC offset of the OPX analog input channel associated with a element.

        Args:
            element (str): the name of the element to update the
                correction for
            output (str): the output key name as appears in the element
                config under 'outputs'.
            offset (float): the dc value to set to, in normalized input
                units. Ranges from -0.5 to 0.5 - 2^-16 in steps of
                2^-16.

        Note:
            If the sum of the DC offset and the largest waveform data-point exceed the normalized unit range specified
            above, DAC output overflow will occur and the output will be corrupted.
        """
        logger.debug(
            "Setting DC offset of output '%s' on element '%s' to '%s'",
            output,
            element,
            offset,
        )
        if type(element) is not str:
            raise TypeError("element must be a string")
        if type(output) is not str:
            raise TypeError("output must be a string")
        if not isinstance(offset, (numpy.floating, float)):
            raise TypeError("offset must be a float")

        offset = _fix_object_data_type(offset)

        self._frontend.set_input_dc_offset(self._id, element, output, offset)

    def get_input_dc_offset_by_element(self, element, output):
        """Get the current DC offset of the OPX analog input channel associated with a element.

        Args:
            element: the name of the element to get the correction for
            output: the output key name as appears in the element config
                under 'outputs'.

        Returns:
            the offset, in normalized output units
        """
        config = self.get_config()

        if element in config["elements"]:
            element_obj = config["elements"][element]
        else:
            raise Exception("Element not found")

        if "outputs" in element_obj:
            outputs = element_obj["outputs"]
        else:
            raise Exception("Element has not outputs")

        if output in outputs:
            port = outputs[output]
        else:
            raise Exception("Output does not exist")

        if port[0] in config["controllers"]:
            controller = config["controllers"][port[0]]
        else:
            raise Exception("Controller does not exist")

        if "analog_inputs" not in controller:
            raise Exception("Controller has not analog inputs defined")

        if port[1] in controller["analog_inputs"]:
            return controller["analog_inputs"][port[1]]["offset"]
        else:
            raise Exception("Port not found")

    def get_digital_delay(self, element, digital_input):
        """Gets the delay of the digital input of the element

        Args:
            element: the name of the element to get the delay for
            digital_input: the digital input name as appears in the
                element's config

        Returns:
            the delay
        """
        element_object = None
        config = self.get_config()
        for (key, value) in config["elements"].items():
            if key == element:
                element_object = value
                break

        if element_object is None:
            raise Exception("element not found")

        for (key, value) in element_object["digitalInputs"].items():
            if key == digital_input:
                return value["delay"]

        raise Exception("digital input not found")

    def set_digital_delay(self, element: str, digital_input: str, delay: int):
        """Sets the delay of the digital input of the element

        Args:
            element (str): the name of the element to update delay for
            digital_input (str): the digital input name as appears in
                the element's config
            delay (int): the delay value to set to, in nsec. Range: 0 to
                255 - 2 * buffer, in steps of 1
        """
        logger.debug(
            "Setting delay of digital port '%s' on element '%s' to '%s'",
            digital_input,
            element,
            delay,
        )
        if type(element) is not str:
            raise Exception("element must be a string")
        if type(digital_input) is not str:
            raise Exception("port must be a string")
        if type(delay) is not int:
            raise Exception("delay must be an int")

        self._frontend.set_digital_delay(self._id, element, digital_input, delay)

    def get_digital_buffer(self, element, digital_input):
        """Gets the buffer for digital input of the element

        Args:
            element (str): the name of the element to get the buffer for
            digital_input (str): the digital input name as appears in
                the element's config

        Returns:
            the buffer
        """
        element_object = None
        config = self.get_config()
        for (key, value) in config["elements"].items():
            if key == element:
                element_object = value
                break

        if element_object is None:
            raise Exception("element not found")

        for (key, value) in element_object["digitalInputs"].items():
            if key == digital_input:
                return value["buffer"]

        raise Exception("digital input not found")

    def set_digital_buffer(self, element, digital_input, buffer):
        """Sets the buffer for digital input of the element

        Args:
            element (str): the name of the element to update buffer for
            digital_input (str): the digital input name as appears in
                the element's config
            buffer (int): the buffer value to set to, in nsec. Range: 0
                to (255 - delay) / 2, in steps of 1
        """
        logger.debug(
            "Setting buffer of digital port '%s' on element '%s' to '%s'",
            digital_input,
            element,
            buffer,
        )
        if type(element) is not str:
            raise Exception("element must be a string")
        if type(digital_input) is not str:
            raise Exception("port must be a string")
        if type(buffer) is not int:
            raise Exception("buffer must be an int")

        self._frontend.set_digital_delay(self._id, element, digital_input, buffer)

    def get_time_of_flight(self, element):
        """Gets the *time of flight*, associated with a measurement element.

        This is the amount of time between the beginning of a measurement pulse applied to element
        and the time that the data is available to the controller for demodulation or streaming.

        Args:
            element (str): the name of the element to get time of flight
                for

        Returns:
            the time of flight, in nsec
        """
        element_object = None
        config = self.get_config()
        for (key, value) in config["elements"].items():
            if key == element:
                if "time_of_flight" in value:
                    return value["time_of_flight"]
                else:
                    return 0

        if element_object is None:
            raise Exception("element not found")

    def get_smearing(self, element):
        """Gets the *smearing* associated with a measurement element.

        This is a broadening of the raw results acquisition window, to account for dispersive broadening
        in the measurement elements (readout resonators etc.) The acquisition window will be broadened
        by this amount on both sides.

        Args:
            element (str): the name of the element to get smearing for

        Returns:
            the smearing, in nesc.
        """
        element_object = None
        config = self.get_config()
        for (key, value) in config["elements"].items():
            if key == element:
                if "smearing" in value:
                    return value["smearing"]
                else:
                    return 0

        if element_object is None:
            raise Exception("element not found")

    def set_io1_value(self, value_1: Union[float, bool, int]):
        """Sets the value of ``IO1``.

        This can be used later inside a QUA program as a QUA variable ``IO1`` without declaration.
        The type of QUA variable is inferred from the python type passed to ``value_1``, according to the following rule:

        int -> int
        float -> fixed
        bool -> bool

        Args:
            value_1 (Union[float,bool,int]): the value to be placed in
                ``IO1``
        """
        self.set_io_values(value_1, None)

    def set_io2_value(self, value_2: Union[float, bool, int]):
        """Sets the value of ``IO1``.

        This can be used later inside a QUA program as a QUA variable ``IO2`` without declaration.
        The type of QUA variable is inferred from the python type passed to ``value_2``, according to the following rule:

        int -> int
        float -> fixed
        bool -> bool

        Args:
            value_2 (Union[float, bool, int]): the value to be placed in
                ``IO1``
        """
        self.set_io_values(None, value_2)

    def set_io_values(
        self,
        value_1: Optional[Union[float, bool, int]],
        value_2: Optional[Union[float, bool, int]],
    ):
        """Sets the values of ``IO1`` and ``IO2``

        This can be used later inside a QUA program as a QUA variable ``IO1``, ``IO2`` without declaration.
        The type of QUA variable is inferred from the python type passed to ``value_1``, ``value_2``,
        according to the following rule:

        int -> int
        float -> fixed
        bool -> bool

        Args:
            value_1 (Optional[Union[float, bool, int]]): the value to be
                placed in ``IO1``
            value_2 (Optional[Union[float, bool, int]]): the value to be
                placed in ``IO2``
        """

        if value_1 is None and value_2 is None:
            return

        if value_1 is not None:
            logger.debug("Setting value '%s' to IO1", value_1)
        if value_2 is not None:
            logger.debug("Setting value '%s' to IO2", value_2)

        value_1 = _fix_object_data_type(value_1)
        value_2 = _fix_object_data_type(value_2)

        for index, value in enumerate([value_1, value_2]):
            if type(value) not in (int, float, bool) and value is not None:
                raise Exception(
                    f"Invalid value_{index + 1} type (The possible types are: int, bool or float)"
                )

        self._frontend.set_io_values(self._id, [value_1, value_2])

    def get_io1_value(self):
        """Gets the data stored in ``IO1``

        No inference is made on type.

        Returns:
            A dictionary with data stored in ``IO1``. (Data is in all
            three format: ``int``, ``float`` and ``bool``)
        """
        return self.get_io_values()[0]

    def get_io2_value(self):
        """Gets the data stored in ``IO2``

        No inference is made on type.

        Returns:
            A dictionary with data from the second IO register. (Data is
            in all three format: ``int``, ``float`` and ``bool``)
        """
        return self.get_io_values()[1]

    def get_io_values(self):
        """Gets the data stored in both ``IO1`` and ``IO2``

        No inference is made on type.

        Returns:
            A list that contains dictionaries with data from the IO
            registers. (Data is in all three format: ``int``, ``float``
            and ``bool``)
        """
        resp1, resp2 = self._frontend.get_io_values(self._id)

        return [
            {
                "io_number": 1,
                "int_value": resp1.int_value,
                "fixed_value": resp1.double_value,
                "boolean_value": resp1.boolean_value,
            },
            {
                "io_number": 2,
                "int_value": resp2.int_value,
                "fixed_value": resp2.double_value,
                "boolean_value": resp2.boolean_value,
            },
        ]

    @deprecated("1.1", "1.2", details="Not implemented")
    def peek(self, address):
        raise NotImplementedError()
        # if you must use this, code below will work for a specific controller
        # request = PeekRequest()
        # request.controllerId = list(self._config["controllers"].keys())[0]
        # request.address = address

        # return self._frontend.Peek(request)

    @deprecated("1.1", "1.2", details="Not implemented")
    def poke(self, address, value):
        pass

    def get_config(self):
        """Gets the current config of the qm

        Returns:
            A dictionary with the qm's config
        """
        config = self._frontend.get_quantum_machine_config(self._id)
        self._config = config
        return convert_msg_to_config(config)

    def save_config_to_file(self, filename):
        """Saves the qm current config to a file

        Args:
            filename: The name of the file where the config will be saved
        """
        json_str = json.dumps(self.get_config())
        with open(filename, "w") as writer:
            writer.write(json_str)

    def get_running_job(self) -> Optional[QmJob]:
        """Gets the currently running job. Returns None if there isn't one."""
        job_id = self._job_manager.get_running_job(self._id)
        if job_id is None:
            return None

        try:
            pending_job = QmPendingJob(
                job_id=job_id,
                machine_id=self._id,
                frontend_api=self._frontend,
                capabilities=self._capabilities,
                store=self._store,
            )
            return pending_job.wait_for_execution(timeout=10.0)
        except JobCancelledError:
            # In case that the job has finished between the GetRunningJon and the
            # wait for execution
            return None

    def set_digital_input_threshold(self, port: Tuple[str, int], threshold: float):
        controller_name, port_number = port
        self._frontend.set_digital_input_threshold(
            self._id, controller_name, port_number, threshold
        )

    def _get_digital_input_port(self, port: Tuple[str, int]):
        config: Dict = self.get_config()
        component = "Controller"
        target_controller_name, target_port = port
        controller = config["controllers"].get(target_controller_name, None)
        if controller is not None:
            controller_digital_inputs = controller.get("digital_inputs", None)
            if controller_digital_inputs is not None:
                if target_port in controller_digital_inputs:
                    return controller_digital_inputs[target_port]
                else:
                    component = "Digital input port"
            else:
                component = "Digital input for conroller"

        raise InvalidConfigError(f"{component} not found")

    def get_digital_input_threshold(self, port: Tuple[str, int]) -> float:
        return self._get_digital_input_port(port)["threshold"]

    def set_digital_input_deadtime(self, port: Tuple[str, int], deadtime: int):
        controller_name, port_number = port
        self._frontend.set_digital_input_dead_time(
            self._id, controller_name, port_number, deadtime
        )

    def get_digital_input_deadtime(self, port: Tuple[str, int]) -> int:
        return self._get_digital_input_port(port)["deadtime"]

    def set_digital_input_polarity(self, port: Tuple[str, int], polarity: str) -> str:
        if polarity == "RISING":
            polarity = Polarity.RISING
        elif polarity == "FALLING":
            polarity = Polarity.FALLING
        else:
            raise InvalidDigitalInputPolarityError(
                f"Invalid value for polarity {polarity}. Valid values are: 'RISING' "
                f"or 'FALLING'"
            )

        controller_name, port_number = port
        self._frontend.set_digital_input_polarity(
            self._id, controller_name, port_number, polarity
        )

    def get_digital_input_polarity(self, port: Tuple[str, int]) -> str:
        return self._get_digital_input_port(port)["polarity"]
