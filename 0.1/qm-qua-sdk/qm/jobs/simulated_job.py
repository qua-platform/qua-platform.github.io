import json as _json
from dataclasses import dataclass
from io import BytesIO
from typing import Dict, Union

import betterproto
import numpy
from betterproto.lib.google.protobuf import Value, Struct
from deprecation import deprecated
from numpy.lib import format as _format

from qm.api.async_thread import CallbackStopIteration
from qm.api.frontend_api import FrontendApi
from qm.api.models.capabilities import ServerCapabilities
from qm.api.simulation_api import SimulationApi
from qm.exceptions import QMSimulationError
from qm.grpc.frontend import SimulatedResponsePart
from qm.grpc.results_analyser import SimulatorSamplesResponse
from qm.jobs.running_qm_job import RunningQmJob
from qm.persistence import BaseStore
from qm.results.simulator_samples import SimulatorSamples
from qm.waveform_report import WaveformReport


@dataclass
class DensityMatrix:
    timestamp: int
    data: numpy.ndarray


class SimulatorOutput:
    def __init__(self, job_id: str, frontend: FrontendApi) -> None:
        super().__init__()
        self._id = job_id
        self._frontend = frontend

    def get_quantum_state(self) -> DensityMatrix:

        state = self._frontend.get_simulated_quantum_state()
        flatten = numpy.array([complex(item.re, item.im) for item in state.data])
        n = int(numpy.sqrt(len(flatten)))
        if len(flatten) != (n * n):
            raise RuntimeError("Quantum state matrix is not correct")
        else:
            pass

        matrix = flatten.reshape(n, n)
        timestamp = state.time_stamp
        return DensityMatrix(timestamp, matrix)


def extract_value(value: Value):
    name, one_of = betterproto.which_one_of(value, "kind")
    if name in VALUE_MAPPING:
        return VALUE_MAPPING[name](one_of)


def extract_struct_value(struct_value: Struct) -> Dict[str, Union[Dict[str, str], str]]:
    output = {}
    for name, value in struct_value.fields.items():
        output[name] = extract_value(value)
    return output


VALUE_MAPPING = {
    "number_value": float,
    "string_value": str,
    "bool_value": bool,
    "list_value": lambda list_value: [
        extract_value(value) for value in list_value.values
    ],
    "struct_value": extract_struct_value,
    "null_value": lambda x: None,
}


class SimulatedJob(RunningQmJob):
    def __init__(
        self,
        job_id: str,
        frontend_api: FrontendApi,
        capabilities: ServerCapabilities,
        store: BaseStore,
        simulated_response: SimulatedResponsePart,
    ):
        super().__init__(job_id, "", frontend_api, capabilities, store)
        self._waveform_report = None

        self._simulated_analog_outputs = {"samples": None, "waveforms": None}
        self._simulated_digital_outputs = {"samples": None, "waveforms": None}
        if betterproto.serialized_on_wire(simulated_response.analog_outputs):
            self._simulated_analog_outputs = extract_struct_value(
                simulated_response.analog_outputs
            )
        if betterproto.serialized_on_wire(simulated_response.digital_outputs):
            self._simulated_digital_outputs = extract_struct_value(
                simulated_response.digital_outputs
            )
        if betterproto.serialized_on_wire(simulated_response.waveform_report):
            self._waveform_report = WaveformReport.from_dict(
                extract_struct_value(simulated_response.waveform_report), self.id
            )
        if simulated_response.errors:
            raise RuntimeError("\n".join(simulated_response.simulated.errors))

        self._simulation_api = SimulationApi.from_api(self._frontend)

    def _initialize_from_job_status(self):
        """
        Overriding this for simulated jobs to do nothing
        """
        pass

    def get_simulated_waveform_report(self) -> WaveformReport:
        return self._waveform_report

    @deprecated("1.1.0", "1.2.0", details="use 'get_simulated_waveform_report'")
    def simulated_analog_waveforms(self):
        """
        Return the results of the simulation of elements and analog outputs.

        The returned dictionary has the following keys and entries:

        - **elements**: a dictionary containing the outputs with timestamps and values arranged by elements.

        - **controllers: a dictionary containing the outputs with timestamps and values arranged by controllers.

            - **ports**: a dictionary containing the outputs with timestamps and values arranged by output ports.
                for each element or output port, the entry is a list of dictionaries with the following information:

                - **timestamp**:
                    The time, in nsec, from the start of the program to the start of the pulse.

                - **samples**:

                    Output information, with ``duration`` given in nsec and ``value`` given normalized OPX output units.

        Returns:
            A dictionary containing output information for the analog outputs of the controller.

        """
        return self._simulated_analog_outputs["waveforms"]

    @deprecated("1.1.0", "1.2.0", details="use 'get_simulated_waveform_report'")
    def simulated_digital_waveforms(self):
        """
        Return the results of the simulation of digital outputs.

        - **controllers**: a dictionary containing the outputs with timestamps and values arranged by controllers.

            - **ports**: a dictionary containing the outputs with timestamps and values arranged by output ports.
                for each element or output port, the entry is a list of dictionaries with the following information:

                - **timestamp**:
                    The time, in nsec, from the start of the program to the start of the pulse.

                - **samples**:
                    A list containing the sequence of outputted values, with ``duration`` given in nsec
                    and ``value`` given as a boolean value.

        Returns:
            A dictionary containing output information for the analog outputs of the controller.
        """
        return self._simulated_digital_outputs["waveforms"]

    def _get_np_simulated_samples(self, include_analog=True, include_digital=True):
        writer = BytesIO()
        data_writer = BytesIO()

        def callback(result: SimulatorSamplesResponse) -> bool:
            if result.ok:
                name, value = betterproto.which_one_of(result, "body")
                if name == "header":
                    _format.write_array_header_2_0(
                        writer,
                        {
                            "descr": _json.loads(value.simple_d_type),
                            "fortran_order": False,
                            "shape": (value.count_of_items,),
                        },
                    )
                elif name == "data":
                    data_writer.write(value.data)

            return result.ok

        try:
            self._simulation_api.pull_simulator_samples(
                self._id, include_analog, include_digital, callback=callback
            )
        except CallbackStopIteration:
            raise QMSimulationError("Error while pulling samples")

        data_writer.seek(0)
        for d in data_writer:
            writer.write(d)

        writer.seek(0)
        return numpy.load(writer)

    def get_simulated_samples(self, include_analog=True, include_digital=True):
        """
        Obtain the output samples of a QUA program simulation.

        Samples are returned in an object that holds the controllers in the current simulation,
        where each controller's name will be a property of this object.
        The value of each property of the returned value is an object with the following properties:

        ``analog``:

            holds a dictionary with analog port names as keys and numpy array of samples as values.

        ``digital``:

            holds a dictionary with digital port names as keys and numpy array of samples as values.

        It is also possible to directly plot the outputs using a built-in plot command.

        Example:
            ```python
            samples = job.get_simulated_samples()
            analog1 = samples.con1.analog["1"]  # obtain analog port 1 of controller "con1"
            digital9 = samples.con1.analog["9"]  # obtain digital port 9 of controller "con1"
            samples.con1.plot()  # Plots all active ports
            samples.con1.plot(analog_ports=['1', '2'], digital_ports=['9'])  # Plots the given output ports
            ```

        !!! Note

            The simulated digital waveforms are delayed by 136ns relative to the real
            output of the OPX.

        Args:
            include_analog: Should we collect simulated analog samples
            include_digital: Should we collect simulated digital samples

        Returns:
            The simulated samples of the job.
        """
        return SimulatorSamples.from_np_array(
            self._get_np_simulated_samples(
                include_analog=include_analog, include_digital=include_digital
            )
        )

    @property
    def simulator(self) -> SimulatorOutput:
        return SimulatorOutput(self._id, self._frontend)
