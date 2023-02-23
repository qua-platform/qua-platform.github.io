from typing import List, Callable
import logging
from qm.StreamMetadata import (
    StreamMetadataError,
    _get_stream_metadata_dict_from_proto_resp,
)
from qm.grpc.results_analyser import (
    JobResultsServiceStub,
    GetJobErrorsRequest,
    GetJobErrorsResponse,
    GetJobErrorsResponseError,
    GetJobNamedResultRequest,
    GetJobNamedResultResponse,
    GetJobStateRequest,
    GetJobNamedResultHeaderRequest,
    GetJobNamedResultHeaderResponse,
    GetProgramMetadataRequest,
    GetJobResultSchemaRequest,
    GetJobDebugDataRequest,
    GetJobStateResponse,
    GetProgramMetadataResponse,
    GetJobResultSchemaResponse,
    GetJobDebugDataResponse,
)
from qm.api.base_api import BaseApi, connection_error_handle
from qm.api.models.server_details import ConnectionDetails

logger = logging.getLogger(__name__)


@connection_error_handle()
class JobResultServiceApi(BaseApi):
    def __init__(self, connection_details: ConnectionDetails):
        super().__init__(connection_details)
        self._stub = JobResultsServiceStub(self._channel)

    def get_job_errors(self, job_id: str) -> List[GetJobErrorsResponseError]:
        request = GetJobErrorsRequest(job_id=job_id)
        response: GetJobErrorsResponse = self._execute_on_stub(
            self._stub.get_job_errors, request
        )
        return response.errors

    def get_job_named_result(
        self,
        job_id: str,
        output_name: str,
        long_offset: int,
        limit: int,
        callback: Callable[[GetJobNamedResultResponse], bool],
    ):
        request = GetJobNamedResultRequest(
            job_id=job_id, output_name=output_name, long_offset=long_offset, limit=limit
        )
        self._execute_iterator_on_stub(
            self._stub.get_job_named_result, callback, request
        )

    def get_job_state(self, job_id: str) -> GetJobStateResponse:
        request = GetJobStateRequest(job_id=job_id)
        response: GetJobStateResponse = self._execute_on_stub(
            self._stub.get_job_state, request
        )
        return response

    def get_named_header(
        self, job_id: str, output_name: str, flat_struct: bool
    ) -> GetJobNamedResultHeaderResponse:
        request = GetJobNamedResultHeaderRequest(
            job_id=job_id, output_name=output_name, flat_format=flat_struct
        )
        response: GetJobNamedResultHeaderResponse = self._execute_on_stub(
            self._stub.get_job_named_result_header, request
        )
        return response

    def get_program_metadata(self, job_id: str):
        request = GetProgramMetadataRequest(job_id=job_id)
        response: GetProgramMetadataResponse = self._execute_on_stub(
            self._stub.get_program_metadata, request
        )

        if response.success:
            metadata_errors = [
                StreamMetadataError(error.error, error.location)
                for error in response.program_stream_metadata.stream_metadata_extraction_error
            ]

            metadata_dict = _get_stream_metadata_dict_from_proto_resp(
                response.program_stream_metadata
            )
            return metadata_errors, metadata_dict
        logger.warning(f"Failed to fetch program metadata for job: {job_id}")
        return [], {}

    def get_job_result_schema(self, job_id: str):
        request = GetJobResultSchemaRequest(job_id=job_id)
        response: GetJobResultSchemaResponse = self._execute_on_stub(
            self._stub.get_job_result_schema, request
        )
        return response

    def get_job_debug_data(
        self, job_id: str, callback: Callable[[GetJobDebugDataResponse], bool]
    ):
        request = GetJobDebugDataRequest(job_id=job_id)

        self._execute_iterator_on_stub(self._stub.get_job_debug_data, callback, request)
