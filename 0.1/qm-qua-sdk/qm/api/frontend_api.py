import dataclasses
import logging
from typing import List, Union, Tuple

from betterproto.lib.google.protobuf import Empty, StringValue

from qm.api.base_api import connection_error_handle, BaseApi
from qm.api.models.compiler import (
    CompilerOptionArguments,
    _get_request_compiler_options,
)
from qm.api.models.devices import MixerInfo, AnalogOutputPortFilter, Polarity
from qm.api.models.jobs import InsertDirection
from qm.api.models.quantum_machine import QuantumMachineData
from qm.api.models.server_details import ConnectionDetails
from qm.exceptions import (
    OpenQmException,
    FailedToAddJobToQueueException,
    CompilationException,
    QMHealthCheckError,
    QMFailedToGetQuantumMachineError,
    QmFailedToCloseQuantumMachineError,
    QMFailedToCloseAllQuantumMachinesError,
    QMRequestError,
    QMConnectionError,
    QMRequestDataError,
)
from qm.grpc.compiler import QuaValues
from qm.grpc.frontend import (
    FrontendStub,
    HealthCheckResponse,
    ResetDataProcessingRequest,
    PerformHalDebugCommandRequest,
    PerformHalDebugCommandResponse,
    AddToQueueRequest,
    QueuePosition,
    ExecutionOverrides,
    AddCompiledToQueueRequest,
    CompileRequest,
    QmDataRequest,
    IoValueRequest,
    AddToQueueResponse,
    AddCompiledToQueueResponse,
    CompileResponse,
    QmDataResponse,
)
from qm.grpc.general_messages import Matrix
from qm.grpc.qm_api import (
    HighQmApiRequest,
    HighQmApiRequestSetCorrection,
    HighQmApiRequestSetCorrectionMixerInfo,
    HighQmApiRequestSetFrequency,
    HighQmApiRequestSetOutputDcOffset,
    HighQmApiRequestQePort,
    HighQmApiRequestSetOutputFilterTaps,
    HighQmApiRequestAnalogOutputPortFilter,
    HighQmApiRequestSetInputDcOffset,
    HighQmApiRequestSetDigitalRoute,
    HighQmApiRequestSetIoValues,
    HighQmApiRequestIoValueSetData,
    HighQmApiRequestSetDigitalInputThreshold,
    DigitalInputPort,
    HighQmApiRequestSetDigitalInputPolarity,
    HighQmApiRequestSetDigitalInputDeadtime,
    HighQmApiResponse,
)
from qm.grpc.qm_manager import (
    OpenQuantumMachineRequest,
    OpenQuantumMachineResponse,
    ListOpenQuantumMachinesResponse,
    GetQuantumMachineRequest,
    GetQuantumMachineResponse,
    CloseAllQuantumMachinesResponse,
    GetControllersResponse,
    CloseQuantumMachineRequest,
    Controller,
    CloseQuantumMachineResponse,
)
from qm.grpc.qua import QuaProgram
from qm.grpc.qua_config import QuaConfig
from qm.utils import _level_map

Value = Union[float, bool, int]

logger = logging.getLogger(__name__)


@connection_error_handle()
class FrontendApi(BaseApi):
    def __init__(self, connection_details: ConnectionDetails):
        super().__init__(connection_details)
        self._stub = FrontendStub(self._channel)

    def get_version(self) -> str:
        response: StringValue = self._execute_on_stub(self._stub.get_version, Empty())
        return response.value

    def healthcheck(self, strict: bool):
        logger.info("Performing health check")
        response: HealthCheckResponse = self._execute_on_stub(
            self._stub.health_check, Empty()
        )

        for warning in response.warning_messages:
            logger.warning(f"Health check warning: {warning}")

        if not response.ok:
            logger.error(f"Health check error: {response.message}")

            for error in response.error_messages:
                logger.error(f"Health check error: {error}")

            if strict:
                raise QMHealthCheckError("Health check failed")
            return

        logger.info("Health check passed")

    def reset_data_processing(self):
        self._execute_on_stub(
            self._stub.reset_data_processing, ResetDataProcessingRequest()
        )

    def open_qm(self, config: QuaConfig, close_other_machines: bool) -> str:
        request = OpenQuantumMachineRequest(
            config=config,
        )

        if close_other_machines:
            request.always = True
        else:
            request.never = True

        response: OpenQuantumMachineResponse = self._execute_on_stub(
            self._stub.open_quantum_machine, request
        )

        if not response.success:
            for error in response.config_validation_errors:
                logger.error(
                    f'CONFIG ERROR in key "{error.path}" [{error.group}] : {error.message}'
                )

            for error in response.physical_validation_errors:
                logger.error(
                    f'PHYSICAL CONFIG ERROR in key "{error.path}" [{error.group}] : {error.message}'
                )

            raise OpenQmException("Can not open QM. Please see previous errors")

        for warning in response.open_qm_warnings:
            logger.warning(
                f"Open QM ended with warning {warning.code}: {warning.message}"
            )

        return response.machine_id

    def list_open_quantum_machines(self) -> List[str]:
        response: ListOpenQuantumMachinesResponse = self._execute_on_stub(
            self._stub.list_open_quantum_machines, Empty()
        )
        return response.machine_i_ds

    def get_quantum_machine(self, qm_id: str) -> QuantumMachineData:
        request = GetQuantumMachineRequest(machine_id=qm_id)
        response: GetQuantumMachineResponse = self._execute_on_stub(
            self._stub.get_quantum_machine, request
        )

        if not response.success:
            error_message = "\n".join([error.message for error in response.errors])
            raise QMFailedToGetQuantumMachineError(
                f"Failed to fetch quantum machine: {error_message}"
            )

        return QuantumMachineData(
            machine_id=response.machine_id, config=response.config
        )

    def close_quantum_machine(self, machine_id: str) -> bool:
        request = CloseQuantumMachineRequest(machine_id=machine_id)
        response: CloseQuantumMachineResponse = self._execute_on_stub(
            self._stub.close_quantum_machine, request
        )
        if not response.success:
            raise QmFailedToCloseQuantumMachineError(
                "\n".join(err.message for err in response.errors)
            )
        return True

    def get_quantum_machine_config(self, machine_id: str) -> QuaConfig:
        machine_data = self.get_quantum_machine(machine_id)
        return machine_data.config

    def close_all_quantum_machines(self):
        response: CloseAllQuantumMachinesResponse = self._execute_on_stub(
            self._stub.close_all_quantum_machines, Empty()
        )
        if not response.success:
            for error in response.errors:
                logger.error(error.message)

            raise QMFailedToCloseAllQuantumMachinesError(
                "Can not close all quantum machines. Please see previous errors"
            )

    def get_controllers(self) -> List[Controller]:
        response: GetControllersResponse = self._execute_on_stub(
            self._stub.get_controllers, Empty()
        )
        return response.controllers

    def clear_all_job_results(self):
        self._execute_on_stub(self._stub.clear_all_job_results, Empty())

    def send_debug_command(self, controller_name: str, command: str) -> str:
        request = PerformHalDebugCommandRequest(
            controller_name=controller_name, command=command
        )
        response: PerformHalDebugCommandResponse = self._execute_on_stub(
            self._stub.perform_hal_debug_command, request
        )

        if not response.success:
            raise QMConnectionError(response.response)
        return response.response

    def add_to_queue(
        self,
        machine_id: str,
        program: QuaProgram,
        compiler_options: CompilerOptionArguments,
        insert_direction: InsertDirection,
    ) -> str:
        queue_position = QueuePosition()
        if insert_direction == InsertDirection.start:
            queue_position.start = Empty()
        elif insert_direction == InsertDirection.end:
            queue_position.end = Empty()

        program.compiler_options = _get_request_compiler_options(compiler_options)

        request = AddToQueueRequest(
            quantum_machine_id=machine_id,
            high_level_program=program,
            queue_position=queue_position,
        )

        logger.info("Sending program to QOP for compilation")

        response: AddToQueueResponse = self._execute_on_stub(
            self._stub.add_to_queue, request
        )

        for message in response.messages:
            logger.log(_level_map[message.level], message.message)

        job_id = response.job_id
        if not response.ok:
            logger.error(f"Job {job_id} failed. Failed to execute program.")
            raise FailedToAddJobToQueueException(
                f"Job {job_id} failed. Failed to execute program."
            )

        return job_id

    def add_compiled_to_queue(
        self, machine_id: str, program_id: str, execution_overrides: ExecutionOverrides
    ) -> str:

        queue_position = QueuePosition()
        queue_position.end = Empty()

        request = AddCompiledToQueueRequest(
            quantum_machine_id=machine_id,
            program_id=program_id,
            queue_position=queue_position,
            execution_overrides=execution_overrides,
        )

        response: AddCompiledToQueueResponse = self._execute_on_stub(
            self._stub.add_compiled_to_queue, request
        )

        job_id = response.job_id

        for err in response.errors:
            logger.error(err.message)

        if not response.ok:
            logger.error(f"Job {job_id} failed. Failed to execute program.")
            raise FailedToAddJobToQueueException(
                f"Job {job_id} failed. Failed to execute program."
            )

        return job_id

    def compile(
        self,
        machine_id: str,
        program: QuaProgram,
        compiler_options: CompilerOptionArguments,
    ) -> str:
        program.compiler_options = _get_request_compiler_options(compiler_options)
        request = CompileRequest(
            quantum_machine_id=machine_id, high_level_program=program
        )

        response: CompileResponse = self._execute_on_stub(self._stub.compile, request)

        for message in response.messages:
            logger.log(_level_map[message.level], message.message)

        program_id = response.program_id
        if not response.ok:
            logger.error(f"Compilation of program {program_id} failed")
            raise CompilationException(f"Compilation of program {program_id} failed")
        return program_id

    def _perform_qm_request(self, request: HighQmApiRequest):
        response: HighQmApiResponse = self._execute_on_stub(
            self._stub.perform_qm_request, request
        )

        if not response.ok:
            error_message = "\n".join(it.message for it in response.errors)
            logger.error(f"Failed: {error_message}")
            raise QMRequestError(f"Failed: {error_message}")

    def set_correction(self, machine_id: str, mixer: MixerInfo, correction: Matrix):
        correction_request = HighQmApiRequestSetCorrection(
            mixer=HighQmApiRequestSetCorrectionMixerInfo(**mixer.as_dict()),
            correction=correction,
        )
        request = HighQmApiRequest(
            quantum_machine_id=machine_id, set_correction=correction_request
        )
        self._perform_qm_request(request)

    def set_intermediate_frequency(self, machine_id: str, element: str, value: float):
        set_frequency_request = HighQmApiRequestSetFrequency(qe=element, value=value)
        request = HighQmApiRequest(
            quantum_machine_id=machine_id, set_frequency=set_frequency_request
        )
        self._perform_qm_request(request)

    def set_output_dc_offset(
        self, machine_id: str, element: str, element_port: str, offset: float
    ):
        output_dc_offset_request = HighQmApiRequestSetOutputDcOffset(
            qe=HighQmApiRequestQePort(qe=element, port=element_port), i=offset, q=offset
        )
        request = HighQmApiRequest(
            quantum_machine_id=machine_id, set_output_dc_offset=output_dc_offset_request
        )
        self._perform_qm_request(request)

    def set_output_filter_taps(
        self,
        machine_id: str,
        element: str,
        element_port: str,
        filter_port: AnalogOutputPortFilter,
    ):
        output_filter_tap_request = HighQmApiRequestSetOutputFilterTaps(
            qe=HighQmApiRequestQePort(qe=element, port=element_port),
            filter=HighQmApiRequestAnalogOutputPortFilter(
                **dataclasses.asdict(filter_port)
            ),
        )
        request = HighQmApiRequest(
            quantum_machine_id=machine_id,
            set_output_filter_taps=output_filter_tap_request,
        )
        self._perform_qm_request(request)

    def set_input_dc_offset(
        self, machine_id: str, element: str, element_port: str, offset: float
    ):
        input_dc_offset_request = HighQmApiRequestSetInputDcOffset(
            qe=HighQmApiRequestQePort(qe=element, port=element_port), offset=offset
        )
        request = HighQmApiRequest(
            quantum_machine_id=machine_id, set_input_dc_offset=input_dc_offset_request
        )
        self._perform_qm_request(request)

    def set_digital_delay(
        self, machine_id: str, element: str, element_port: str, delay: int
    ):
        digital_delay_request = HighQmApiRequestSetDigitalRoute(
            delay=HighQmApiRequestQePort(qe=element, port=element_port), value=delay
        )
        request = HighQmApiRequest(
            quantum_machine_id=machine_id, set_digital_route=digital_delay_request
        )
        self._perform_qm_request(request)

    def set_digital_buffer(
        self, machine_id: str, element: str, element_port: str, buffer: int
    ):
        digital_buffer_request = HighQmApiRequestSetDigitalRoute(
            buffer=HighQmApiRequestQePort(qe=element, port=element_port), value=buffer
        )
        request = HighQmApiRequest(
            quantum_machine_id=machine_id, set_digital_route=digital_buffer_request
        )
        self._perform_qm_request(request)

    def set_io_values(self, machine_id: str, values: List[Value]):
        type_to_value_mapping = {
            int: "int_value",
            float: "double_value",
            bool: "boolean_value",
        }

        set_data = [
            HighQmApiRequestIoValueSetData(
                io_number=index + 1, **{type_to_value_mapping[type(value)]: value}
            )
            for index, value in enumerate(values)
            if value is not None
        ]

        set_io_values = HighQmApiRequestSetIoValues(
            all=True, io_value_set_data=set_data
        )
        request = HighQmApiRequest(
            quantum_machine_id=machine_id, set_io_values=set_io_values
        )
        self._perform_qm_request(request)

    def set_digital_input_threshold(
        self, machine_id: str, controller_name: str, port_number: int, threshold: float
    ):
        digital_input_threshold_request = HighQmApiRequestSetDigitalInputThreshold(
            digital_port=DigitalInputPort(
                controller_name=controller_name, port_number=port_number
            ),
            threshold=threshold,
        )
        request = HighQmApiRequest(
            quantum_machine_id=machine_id,
            set_digital_input_threshold=digital_input_threshold_request,
        )
        self._perform_qm_request(request)

    def set_digital_input_dead_time(
        self, machine_id: str, controller_name: str, port_number: int, dead_time: int
    ):
        digital_input_dead_time_request = HighQmApiRequestSetDigitalInputDeadtime(
            digital_port=DigitalInputPort(
                controller_name=controller_name, port_number=port_number
            ),
            deadtime=dead_time,
        )
        request = HighQmApiRequest(
            quantum_machine_id=machine_id,
            set_digital_input_deadtime=digital_input_dead_time_request,
        )
        self._perform_qm_request(request)

    def set_digital_input_polarity(
        self,
        machine_id: str,
        controller_name: str,
        port_number: int,
        polarity: Polarity,
    ):
        digital_input_polarity_request = HighQmApiRequestSetDigitalInputPolarity(
            digital_port=DigitalInputPort(
                controller_name=controller_name, port_number=port_number
            ),
            polarity=polarity.value,
        )
        request = HighQmApiRequest(
            quantum_machine_id=machine_id,
            set_digital_input_polarity=digital_input_polarity_request,
        )
        self._perform_qm_request(request)

    def get_io_values(self, machine_id: str) -> Tuple[QuaValues, ...]:
        request = QmDataRequest(
            io_value_request=[
                IoValueRequest(io_number=1, quantum_machine_id=machine_id),
                IoValueRequest(io_number=2, quantum_machine_id=machine_id),
            ]
        )
        response: QmDataResponse = self._execute_on_stub(
            self._stub.request_data, request
        )

        if not response.success:
            raise QMRequestDataError("\n".join(err.message for err in response.errors))

        return tuple(resp.values for resp in response.io_value_response)
