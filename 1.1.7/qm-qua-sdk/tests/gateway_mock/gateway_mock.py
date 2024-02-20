import asyncio
from asyncio import Future
from typing import Optional
from unittest.mock import MagicMock

from betterproto.lib.google.protobuf import Empty
from grpclib.server import Server

from qm.grpc.frontend import FrontendBase
from qm.grpc.job_manager import JobManagerServiceBase
from qm.grpc.results_analyser import JobResultsServiceBase
from qm.io.qualang.api.v1 import InfoServiceBase, GetInfoResponse, ImplementationDetails
from qm.utils.async_utils import create_future
from tests.gateway_mock.base_responses import (
    BASE_GET_VERSION_RESPONSE,
    BASE_HEALTH_CHECK_RESPONSE,
    BASE_EXECUTION_RESPONSE,
    BASE_ADD_TO_QUEUE_RESPONSE,
    BASE_OPEN_QUANTUM_MACHINE_RESPONSE,
    BASE_COMPILE_RESPONSE,
    BASE_ADD_COMPILED_TO_QUEUE_RESPONSE,
    BASE_REMOVE_PENDING_JOBS_RESPONSE,
    BASE_GET_PENDING_JOBS_RESPONSE,
    BASE_GET_JOB_EXECUTION_STATUS_RESPONSE,
    BASE_GET_PAUSED_STATUS_RESPONSE,
    BASE_RESUME_RESPONSE,
    BASE_HALT_STATUS,
    BASE_RESET_DATA_PROCESSING_RESPONSE,
    BASE_VALIDATION_CONFIG_RESPONSE,
    BASE_PERFORM_QM_REQUEST_RESPONSE,
    BASE_REQUEST_DATA_RESPONSE,
    BASE_PULL_SIMULATOR_SAMPLES_RESPONSE,
    BASE_CLOSE_QUANTUM_MACHINE_RESPONSE,
    BASE_GET_QUANTUM_MACHINE_RESPONSE,
    BASE_GET_RUNNING_JOB_RESPONSE,
    BASE_LIST_OPEN_QUANTUM_MACHINES_RESPONSE,
    BASE_CLOSE_ALL_QUANTUM_MACHINES_RESPONSE,
    BASE_GET_CONTROLLERS_RESPONSE,
    BASE_IS_JOB_RUNNING_RESPONSE,
    BASE_IS_JOB_ACQUIRING_DATA_RESPONSE,
    BASE_SIMULATE_RESPONSE,
    BASE_PERFORM_HAL_DEBUG_COMMAND_RESPONSE,
    BASE_GET_SIMULATED_QUANTUM_STATE_RESPONSE,
)


class EndpointMock:
    def __init__(self, response=None, delay=0.0):
        self.mock = MagicMock()
        self.response = response
        self.delay = delay

    def reset_mock(self):
        self.mock.reset_mock()
        self.mock.return_value = self.response

    async def __call__(self, *args, **kwargs):
        ret = self.mock(*args, **kwargs)
        await asyncio.sleep(self.delay)
        return ret


class BaseMockService:
    def __init__(self):
        self._delay = 0.0
        self.reset()

    def reset(self):
        for attr in self.__dict__.values():
            if isinstance(attr, EndpointMock):
                attr.reset_mock()
                attr.delay = 0.0
        self._delay = 0.0

    @property
    def delay(self):
        return self._delay

    @delay.setter
    def delay(self, new_delay):
        self._delay = new_delay
        for attr in self.__dict__.values():
            if isinstance(attr, EndpointMock):
                attr.delay = new_delay


class InfoServiceMock(BaseMockService, InfoServiceBase):
    def __init__(self):
        self.get_info = EndpointMock(
            GetInfoResponse(
                implementation=ImplementationDetails(name="mock", version="1.3.3.7", url="something"), capabilities=[]
            )
        )
        super().__init__()


class JobManagerMock(BaseMockService, JobManagerServiceBase):
    def __init__(self):
        self.get_element_correction = EndpointMock()
        self.set_element_correction = EndpointMock()
        self.insert_input_stream = EndpointMock()

        super().__init__()


class JobResultServiceMock(BaseMockService, JobResultsServiceBase):
    def __init__(self):
        self.get_job_result_schema = EndpointMock()
        self.get_job_state = EndpointMock()
        self.get_job_named_result_header = EndpointMock()
        self.get_job_named_result = EndpointMock()
        self.get_job_errors = EndpointMock()
        self.get_program_metadata = EndpointMock()

        super().__init__()


class FrontendMock(BaseMockService, FrontendBase):
    def __init__(self):
        self.get_version = EndpointMock(BASE_GET_VERSION_RESPONSE)
        self.health_check = EndpointMock(BASE_HEALTH_CHECK_RESPONSE)
        self.execute = EndpointMock(BASE_EXECUTION_RESPONSE)
        self.add_to_queue = EndpointMock(BASE_ADD_TO_QUEUE_RESPONSE)
        self.compile = EndpointMock(BASE_COMPILE_RESPONSE)
        self.add_compiled_to_queue = EndpointMock(BASE_ADD_COMPILED_TO_QUEUE_RESPONSE)
        self.remove_pending_jobs = EndpointMock(BASE_REMOVE_PENDING_JOBS_RESPONSE)
        self.get_pending_jobs = EndpointMock(BASE_GET_PENDING_JOBS_RESPONSE)
        self.get_job_execution_status = EndpointMock(BASE_GET_JOB_EXECUTION_STATUS_RESPONSE)
        self.paused_status = EndpointMock(BASE_GET_PAUSED_STATUS_RESPONSE)
        self.resume = EndpointMock(BASE_RESUME_RESPONSE)
        self.halt = EndpointMock(BASE_HALT_STATUS)
        self.reset_data_processing = EndpointMock(BASE_RESET_DATA_PROCESSING_RESPONSE)
        self.validate_config = EndpointMock(BASE_VALIDATION_CONFIG_RESPONSE)
        self.init = EndpointMock(Empty())
        self.perform_qm_request = EndpointMock(BASE_PERFORM_QM_REQUEST_RESPONSE)
        self.request_data = EndpointMock(BASE_REQUEST_DATA_RESPONSE)
        self.pull_simulator_samples = EndpointMock(BASE_PULL_SIMULATOR_SAMPLES_RESPONSE)
        self.open_quantum_machine = EndpointMock(BASE_OPEN_QUANTUM_MACHINE_RESPONSE)
        self.close_quantum_machine = EndpointMock(BASE_CLOSE_QUANTUM_MACHINE_RESPONSE)
        self.get_quantum_machine = EndpointMock(BASE_GET_QUANTUM_MACHINE_RESPONSE)
        self.get_running_job = EndpointMock(BASE_GET_RUNNING_JOB_RESPONSE)
        self.list_open_quantum_machines = EndpointMock(BASE_LIST_OPEN_QUANTUM_MACHINES_RESPONSE)
        self.close_quantum_machine = EndpointMock(BASE_CLOSE_ALL_QUANTUM_MACHINES_RESPONSE)
        self.get_controllers = EndpointMock(BASE_GET_CONTROLLERS_RESPONSE)
        self.is_job_running = EndpointMock(BASE_IS_JOB_RUNNING_RESPONSE)
        self.is_job_acquiring_data = EndpointMock(BASE_IS_JOB_ACQUIRING_DATA_RESPONSE)
        self.simulate = EndpointMock(BASE_SIMULATE_RESPONSE)
        self.clear_all_job_results = EndpointMock(Empty())
        self.perform_hal_debug_command = EndpointMock(BASE_PERFORM_HAL_DEBUG_COMMAND_RESPONSE)
        self.get_simulated_quantum_state = EndpointMock(BASE_GET_SIMULATED_QUANTUM_STATE_RESPONSE)

        super().__init__()


class GatewayMock:
    PORT = 1337
    HOST = "127.0.0.1"

    def __init__(self):
        self.frontend = FrontendMock()
        self.info_service = InfoServiceMock()
        self.job_manager = JobManagerMock()
        self.job_result_service = JobResultServiceMock()
        self.future: Optional[Future] = None

    async def _start_server(self):
        server = Server([self.frontend, self.info_service, self.job_manager, self.job_result_service])
        await server.start(self.HOST, self.PORT)
        await server.wait_closed()

    def start(self):
        self.future = create_future(self._start_server())

    def stop(self):
        self.future.cancel()

    def reset_mocks(self):
        for attr in self.__dict__.values():
            if isinstance(attr, BaseMockService):
                attr.reset()
