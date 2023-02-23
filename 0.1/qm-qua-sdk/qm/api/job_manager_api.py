import logging
from typing import Union, List, Optional

from dependency_injector.wiring import Provide

from qm._QmJobErrors import (
    MissingElementError,
    ElementWithSingleInputError,
    InvalidElementCorrectionError,
    ElementWithoutIntermediateFrequencyError,
    _handle_job_manager_error,
    MissingJobError,
    InvalidJobExecutionStatusError,
    UnknownInputStreamError,
)
from qm.api.base_api import BaseApi, connection_error_handle
from qm.api.models.capabilities import ServerCapabilities
from qm.api.models.jobs import PendingJobData
from qm.api.models.server_details import ConnectionDetails
from qm.containers.capabilities_container import CapabilitiesContainer
from qm.exceptions import QmValueError
from qm.grpc.frontend import (
    FrontendStub,
    HaltRequest,
    ResumeRequest,
    PausedStatusRequest,
    IsJobRunningRequest,
    IsJobAcquiringDataResponseAcquiringStatus,
    IsJobAcquiringDataRequest,
    JobExecutionStatus,
    GetJobExecutionStatusRequest,
    JobQueryParams,
    QueryValueMatcher,
    HaltResponse,
    PausedStatusResponse,
    IsJobRunningResponse,
    IsJobAcquiringDataResponse,
    GetJobExecutionStatusResponse,
    RemovePendingJobsResponse,
    GetPendingJobsResponse,
)
from qm.grpc.general_messages import Matrix
from qm.grpc.job_manager import (
    JobManagerServiceStub,
    SetElementCorrectionRequest,
    GetElementCorrectionRequest,
    InsertInputStreamRequest,
    SetElementCorrectionResponse,
    GetElementCorrectionResponse,
    InsertInputStreamResponse,
)
from qm.grpc.qm_manager import GetRunningJobRequest, GetRunningJobResponse

logger = logging.getLogger(__name__)


@connection_error_handle()
class JobManagerApi(BaseApi):
    def __init__(
        self,
        connection_details: ConnectionDetails,
        capabilities: ServerCapabilities = Provide[CapabilitiesContainer.capabilities],
    ):
        super().__init__(connection_details)
        if capabilities.supports_new_grpc_structure:
            self._job_manager_stub = JobManagerServiceStub(self._channel)
        else:
            from qm.api.stubs.deprecated_job_manager_stub import (
                DeprecatedJobManagerServiceStub,
            )

            # TODO: add deprecation warning
            self._job_manager_stub = DeprecatedJobManagerServiceStub(self._channel)
        self._frontend_stub = FrontendStub(self._channel)

    def set_element_correction(
        self, job_id: str, element_name: str, correction: Matrix
    ):
        request = SetElementCorrectionRequest(
            job_id=job_id, qe_name=element_name, correction=correction
        )

        response: SetElementCorrectionResponse = self._execute_on_stub(
            self._job_manager_stub.set_element_correction, request
        )

        valid_errors = (
            MissingElementError,
            ElementWithSingleInputError,
            InvalidElementCorrectionError,
            ElementWithoutIntermediateFrequencyError,
        )
        _handle_job_manager_error(request, response, valid_errors)
        return (
            response.correction.v00,
            response.correction.v01,
            response.correction.v10,
            response.correction.v11,
        )

    def get_element_correction(self, job_id: str, element_name: str):
        request = GetElementCorrectionRequest(job_id=job_id, qe_name=element_name)

        response: GetElementCorrectionResponse = self._execute_on_stub(
            self._job_manager_stub.get_element_correction, request
        )
        valid_errors = (
            MissingElementError,
            ElementWithSingleInputError,
            ElementWithoutIntermediateFrequencyError,
        )
        _handle_job_manager_error(request, response, valid_errors)
        return (
            response.correction.v00,
            response.correction.v01,
            response.correction.v10,
            response.correction.v11,
        )

    def insert_input_stream(
        self, job_id: str, stream_name: str, data: List[Union[int, float, bool]]
    ):
        request = InsertInputStreamRequest(
            job_id=job_id, stream_name=f"input_stream_{stream_name}"
        )

        if all(type(element) == bool for element in data):
            request.bool_stream_data.data.extend(data)
        elif all(type(element) == int for element in data):
            request.int_stream_data.data.extend(data)
        elif all(type(element) == float for element in data):
            request.fixed_stream_data.data.extend(data)
        else:
            raise QmValueError(
                f"Invalid type in data, type is '{set(type(el) for el in data)}', "
                f"excepted types are bool | int | float"
            )

        response: InsertInputStreamResponse = self._execute_on_stub(
            self._job_manager_stub.insert_input_stream, request
        )

        valid_errors = (
            MissingJobError,
            InvalidJobExecutionStatusError,
            UnknownInputStreamError,
        )
        _handle_job_manager_error(request, response, valid_errors)

    def halt(self, job_id: str) -> bool:
        request = HaltRequest(job_id=job_id)
        response: HaltResponse = self._execute_on_stub(
            self._frontend_stub.halt, request
        )
        return response.ok

    def resume(self, job_id: str) -> bool:
        request = ResumeRequest(job_id=job_id)
        self._execute_on_stub(self._frontend_stub.resume, request)
        return True

    def is_paused(self, job_id: str):
        request = PausedStatusRequest(job_id=job_id)
        response: PausedStatusResponse = self._execute_on_stub(
            self._frontend_stub.paused_status, request
        )
        return response.is_paused

    def is_job_running(self, job_id: str):
        request = IsJobRunningRequest(job_id=job_id)

        response: IsJobRunningResponse = self._execute_on_stub(
            self._frontend_stub.is_job_running, request
        )
        return response.is_running

    def is_data_acquiring(
        self, job_id: str
    ) -> IsJobAcquiringDataResponseAcquiringStatus:
        request = IsJobAcquiringDataRequest(job_id=job_id)
        response: IsJobAcquiringDataResponse = self._execute_on_stub(
            self._frontend_stub.is_job_acquiring_data, request
        )
        return response.acquiring_status

    def get_job_execution_status(
        self, job_id: str, quantum_machine_id: str
    ) -> JobExecutionStatus:
        request = GetJobExecutionStatusRequest(
            job_id=job_id, quantum_machine_id=quantum_machine_id
        )
        response: GetJobExecutionStatusResponse = self._execute_on_stub(
            self._frontend_stub.get_job_execution_status, request
        )
        return response.status

    @staticmethod
    def _create_job_query_params(
        quantum_machine_id: str,
        job_id: Optional[str],
        position: Optional[int],
        user_id: Optional[str],
    ):
        request = JobQueryParams(quantum_machine_id=quantum_machine_id)

        if position is not None:
            request.position = position

        if job_id is not None:
            request.job_id = QueryValueMatcher(value=job_id)

        if user_id is not None:
            request.user_id = QueryValueMatcher(value=user_id)

        return request

    def remove_job(
        self,
        quantum_machine_id: str,
        job_id: Optional[str] = None,
        position: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> int:
        request = JobManagerApi._create_job_query_params(
            quantum_machine_id, job_id, position, user_id
        )

        response: RemovePendingJobsResponse = self._execute_on_stub(
            self._frontend_stub.remove_pending_jobs, request
        )
        return response.numbers_of_jobs_removed

    def get_pending_jobs(
        self,
        quantum_machine_id: str,
        job_id: Optional[str],
        position: Optional[int],
        user_id: Optional[str],
    ) -> List[PendingJobData]:

        request = JobManagerApi._create_job_query_params(
            quantum_machine_id, job_id, position, user_id
        )
        response: GetPendingJobsResponse = self._execute_on_stub(
            self._frontend_stub.get_pending_jobs, request
        )
        return [
            PendingJobData(
                job_id=job_id,
                position_in_queue=status.position_in_queue,
                time_added=status.time_added,
                added_by=status.added_by,
            )
            for job_id, status in response.pending_jobs.items()
        ]

    def get_running_job(self, machine_id: str) -> Optional[str]:
        request = GetRunningJobRequest(machine_id=machine_id)
        response: GetRunningJobResponse = self._execute_on_stub(
            self._frontend_stub.get_running_job, request
        )

        if response.job_id:
            return response.job_id
        return None
