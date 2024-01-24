# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: qm/pb/job_results.proto
# plugin: python-betterproto
import warnings
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    AsyncIterator,
    Dict,
    List,
    Optional,
)

import betterproto
import betterproto.lib.google.protobuf as betterproto_lib_google_protobuf
import grpclib
from betterproto.grpc.grpclib_server import ServiceBase

from .. import general_messages as _general_messages__


if TYPE_CHECKING:
    import grpclib.server
    from betterproto.grpc.grpclib_client import MetadataLike
    from grpclib.metadata import Deadline


class GetJobErrorsResponseExecutionErrorSeverity(betterproto.Enum):
    ERROR = 0
    WARNING = 1


@dataclass(eq=False, repr=False)
class GetProgramMetadataRequest(betterproto.Message):
    job_id: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class GetProgramMetadataResponse(betterproto.Message):
    success: bool = betterproto.bool_field(1)
    job_id: str = betterproto.string_field(2)
    program_stream_metadata: "ProgramStreamMetadata" = betterproto.message_field(3)


@dataclass(eq=False, repr=False)
class ProgramStreamMetadata(betterproto.Message):
    stream_metadata: List["StreamMetadata"] = betterproto.message_field(1)
    stream_metadata_extraction_error: List[
        "StreamMetadataExtractionError"
    ] = betterproto.message_field(2)


@dataclass(eq=False, repr=False)
class StreamMetadata(betterproto.Message):
    stream_name: str = betterproto.string_field(1)
    iteration_data: List["IterationData"] = betterproto.message_field(2)


@dataclass(eq=False, repr=False)
class StreamMetadataExtractionError(betterproto.Message):
    location: str = betterproto.string_field(1)
    error: str = betterproto.string_field(2)


@dataclass(eq=False, repr=False)
class IterationData(betterproto.Message):
    iteration_variable_name: str = betterproto.string_field(1)
    for_each_int_iteration_values: "IterationDataForEachIntIterationValues" = (
        betterproto.message_field(2, group="iterationValues")
    )
    for_int_iteration_values: "IterationDataForIntIterationValues" = (
        betterproto.message_field(3, group="iterationValues")
    )
    for_each_double_iteration_values: "IterationDataForEachDoubleIterationValues" = (
        betterproto.message_field(4, group="iterationValues")
    )
    for_double_iteration_values: "IterationDataForDoubleIterationValues" = (
        betterproto.message_field(5, group="iterationValues")
    )


@dataclass(eq=False, repr=False)
class IterationDataForEachIntIterationValues(betterproto.Message):
    values: List[int] = betterproto.int32_field(1)


@dataclass(eq=False, repr=False)
class IterationDataForIntIterationValues(betterproto.Message):
    start_value: int = betterproto.int32_field(1)
    step: int = betterproto.int32_field(2)
    number_of_iterations: int = betterproto.int32_field(3)


@dataclass(eq=False, repr=False)
class IterationDataForEachDoubleIterationValues(betterproto.Message):
    values: List[float] = betterproto.double_field(1)


@dataclass(eq=False, repr=False)
class IterationDataForDoubleIterationValues(betterproto.Message):
    start_value: float = betterproto.double_field(1)
    step: float = betterproto.double_field(2)
    number_of_iterations: int = betterproto.int32_field(3)


@dataclass(eq=False, repr=False)
class GetJobResultSchemaRequest(betterproto.Message):
    job_id: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class GetJobResultSchemaResponse(betterproto.Message):
    items: List["GetJobResultSchemaResponseItem"] = betterproto.message_field(1)


@dataclass(eq=False, repr=False)
class GetJobResultSchemaResponseItem(betterproto.Message):
    name: str = betterproto.string_field(1)
    simple_d_type: str = betterproto.string_field(2)
    is_single: bool = betterproto.bool_field(3)
    expected_count: int = betterproto.int32_field(4)
    shape: List[int] = betterproto.int32_field(5)


@dataclass(eq=False, repr=False)
class GetJobStateRequest(betterproto.Message):
    job_id: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class GetJobStateResponse(betterproto.Message):
    done: bool = betterproto.bool_field(1)
    closed: bool = betterproto.bool_field(2)
    has_dataloss: bool = betterproto.bool_field(3)


@dataclass(eq=False, repr=False)
class GetJobNamedResultHeaderRequest(betterproto.Message):
    job_id: str = betterproto.string_field(1)
    output_name: str = betterproto.string_field(2)
    flat_format: bool = betterproto.bool_field(3)


@dataclass(eq=False, repr=False)
class GetJobNamedResultHeaderResponse(betterproto.Message):
    is_single: bool = betterproto.bool_field(1)
    count_so_far: int = betterproto.int32_field(2)
    simple_d_type: str = betterproto.string_field(3)
    done: bool = betterproto.bool_field(4)
    closed: bool = betterproto.bool_field(5)
    has_dataloss: bool = betterproto.bool_field(6)
    shape: List[int] = betterproto.int32_field(7)
    has_execution_errors: Optional[bool] = betterproto.message_field(
        8, wraps=betterproto.TYPE_BOOL
    )

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.is_set("done"):
            warnings.warn(
                "GetJobNamedResultHeaderResponse.done is deprecated", DeprecationWarning
            )
        if self.is_set("closed"):
            warnings.warn(
                "GetJobNamedResultHeaderResponse.closed is deprecated",
                DeprecationWarning,
            )


@dataclass(eq=False, repr=False)
class GetJobNamedResultRequest(betterproto.Message):
    job_id: str = betterproto.string_field(1)
    output_name: str = betterproto.string_field(2)
    offset: int = betterproto.int32_field(3)
    limit: int = betterproto.int32_field(4)
    long_offset: Optional[int] = betterproto.message_field(
        5, wraps=betterproto.TYPE_INT64
    )

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.is_set("offset"):
            warnings.warn(
                "GetJobNamedResultRequest.offset is deprecated", DeprecationWarning
            )


@dataclass(eq=False, repr=False)
class GetJobNamedResultResponse(betterproto.Message):
    count_of_items: int = betterproto.int32_field(1)
    data: bytes = betterproto.bytes_field(2)


@dataclass(eq=False, repr=False)
class GetJobErrorsRequest(betterproto.Message):
    job_id: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class GetJobErrorsResponse(betterproto.Message):
    errors: List["GetJobErrorsResponseError"] = betterproto.message_field(1)
    job_id: str = betterproto.string_field(2)


@dataclass(eq=False, repr=False)
class GetJobErrorsResponseError(betterproto.Message):
    error_code: int = betterproto.int32_field(1)
    error_severity: "GetJobErrorsResponseExecutionErrorSeverity" = (
        betterproto.enum_field(2)
    )
    message: str = betterproto.string_field(3)


@dataclass(eq=False, repr=False)
class PullAnalysedResultsRequest(betterproto.Message):
    job_file_path: str = betterproto.string_field(1)
    metadata: str = betterproto.string_field(2)
    contains_version: bool = betterproto.bool_field(3)


@dataclass(eq=False, repr=False)
class AnalysedResultsResponse(betterproto.Message):
    version: str = betterproto.string_field(1)
    icp_results: List["IcpResultData"] = betterproto.message_field(11)
    stream_results: List["StreamResultData"] = betterproto.message_field(12)
    errors: List["_general_messages__.ErrorMessage"] = betterproto.message_field(13)


@dataclass(eq=False, repr=False)
class PullResultOutputRequest(betterproto.Message):
    job_id: str = betterproto.string_field(1)
    output_name: str = betterproto.string_field(2)


@dataclass(eq=False, repr=False)
class PullResultOutputResponse(betterproto.Message):
    data: "PullResultOutputResponseData" = betterproto.message_field(
        1, group="response"
    )
    header: "PullResultOutputResponseHeader" = betterproto.message_field(
        2, group="response"
    )
    npz: "PullResultOutputResponseNpz" = betterproto.message_field(3, group="response")
    npy: "PullResultOutputResponseNpy" = betterproto.message_field(4, group="response")


@dataclass(eq=False, repr=False)
class PullResultOutputResponseHeader(betterproto.Message):
    version: str = betterproto.string_field(1)
    output_name: str = betterproto.string_field(2)
    data_loss: bool = betterproto.bool_field(3)
    errors: List["_general_messages__.ErrorMessage"] = betterproto.message_field(4)
    single: bool = betterproto.bool_field(5)


@dataclass(eq=False, repr=False)
class PullResultOutputResponseData(betterproto.Message):
    results: "betterproto_lib_google_protobuf.Value" = betterproto.message_field(1)


@dataclass(eq=False, repr=False)
class PullResultOutputResponseNpz(betterproto.Message):
    npz: bytes = betterproto.bytes_field(1)


@dataclass(eq=False, repr=False)
class PullResultOutputResponseNpy(betterproto.Message):
    name: str = betterproto.string_field(1)
    npy: bytes = betterproto.bytes_field(2)
    count: int = betterproto.int64_field(3)


@dataclass(eq=False, repr=False)
class BinaryWrapper(betterproto.Message):
    data: List[bytes] = betterproto.bytes_field(1)


@dataclass(eq=False, repr=False)
class PullFileResultRequest(betterproto.Message):
    job_id: str = betterproto.string_field(1)
    metadata: str = betterproto.string_field(2)
    as_npz: bool = betterproto.bool_field(4, group="fileType")


@dataclass(eq=False, repr=False)
class FileResultResponse(betterproto.Message):
    job_id: str = betterproto.string_field(1)
    controller_name: str = betterproto.string_field(2)
    group: str = betterproto.string_field(3)
    npz: bytes = betterproto.bytes_field(4, group="file")
    version: str = betterproto.string_field(10)
    errors: List["_general_messages__.ErrorMessage"] = betterproto.message_field(11)


@dataclass(eq=False, repr=False)
class PullSimulatorSamplesRequest(betterproto.Message):
    job_id: str = betterproto.string_field(1)
    include_analog: bool = betterproto.bool_field(2)
    include_digital: bool = betterproto.bool_field(3)
    as_npz: bool = betterproto.bool_field(4, group="fileType")
    include_all_connections: bool = betterproto.bool_field(5)


@dataclass(eq=False, repr=False)
class SimulatorSamplesResponse(betterproto.Message):
    job_id: str = betterproto.string_field(1)
    ok: bool = betterproto.bool_field(5)
    header: "SimulatorSamplesResponseHeader" = betterproto.message_field(
        6, group="body"
    )
    data: "SimulatorSamplesResponseData" = betterproto.message_field(7, group="body")


@dataclass(eq=False, repr=False)
class SimulatorSamplesResponseHeader(betterproto.Message):
    simple_d_type: str = betterproto.string_field(1)
    count_of_items: int = betterproto.int32_field(2)


@dataclass(eq=False, repr=False)
class SimulatorSamplesResponseData(betterproto.Message):
    data: bytes = betterproto.bytes_field(8)


@dataclass(eq=False, repr=False)
class IcpResultData(betterproto.Message):
    name: str = betterproto.string_field(1)
    timestamp: int = betterproto.uint64_field(2)
    data_loss: bool = betterproto.bool_field(3)
    int_value: int = betterproto.int32_field(11, group="data")
    double_value: float = betterproto.double_field(12, group="data")
    boolean_value: bool = betterproto.bool_field(13, group="data")


@dataclass(eq=False, repr=False)
class StreamResultData(betterproto.Message):
    name: str = betterproto.string_field(1)
    timestamp: int = betterproto.uint64_field(2)
    data_loss: bool = betterproto.bool_field(3)
    multiple_sources: bool = betterproto.bool_field(4)
    data_source_name: str = betterproto.string_field(5)
    data: int = betterproto.int64_field(11)


class JobResultsServiceStub(betterproto.ServiceStub):
    async def get_job_result_schema(
        self,
        get_job_result_schema_request: "GetJobResultSchemaRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "GetJobResultSchemaResponse":
        return await self._unary_unary(
            "/qm.grpc.results_analyser.JobResultsService/GetJobResultSchema",
            get_job_result_schema_request,
            GetJobResultSchemaResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def get_job_state(
        self,
        get_job_state_request: "GetJobStateRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "GetJobStateResponse":
        return await self._unary_unary(
            "/qm.grpc.results_analyser.JobResultsService/GetJobState",
            get_job_state_request,
            GetJobStateResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def get_job_named_result_header(
        self,
        get_job_named_result_header_request: "GetJobNamedResultHeaderRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "GetJobNamedResultHeaderResponse":
        return await self._unary_unary(
            "/qm.grpc.results_analyser.JobResultsService/GetJobNamedResultHeader",
            get_job_named_result_header_request,
            GetJobNamedResultHeaderResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def get_job_named_result(
        self,
        get_job_named_result_request: "GetJobNamedResultRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> AsyncIterator["GetJobNamedResultResponse"]:
        async for response in self._unary_stream(
            "/qm.grpc.results_analyser.JobResultsService/GetJobNamedResult",
            get_job_named_result_request,
            GetJobNamedResultResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        ):
            yield response

    async def get_job_errors(
        self,
        get_job_errors_request: "GetJobErrorsRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "GetJobErrorsResponse":
        return await self._unary_unary(
            "/qm.grpc.results_analyser.JobResultsService/GetJobErrors",
            get_job_errors_request,
            GetJobErrorsResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def get_program_metadata(
        self,
        get_program_metadata_request: "GetProgramMetadataRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "GetProgramMetadataResponse":
        return await self._unary_unary(
            "/qm.grpc.results_analyser.JobResultsService/GetProgramMetadata",
            get_program_metadata_request,
            GetProgramMetadataResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )


class JobResultsServiceBase(ServiceBase):
    async def get_job_result_schema(
        self, get_job_result_schema_request: "GetJobResultSchemaRequest"
    ) -> "GetJobResultSchemaResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def get_job_state(
        self, get_job_state_request: "GetJobStateRequest"
    ) -> "GetJobStateResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def get_job_named_result_header(
        self, get_job_named_result_header_request: "GetJobNamedResultHeaderRequest"
    ) -> "GetJobNamedResultHeaderResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def get_job_named_result(
        self, get_job_named_result_request: "GetJobNamedResultRequest"
    ) -> AsyncIterator["GetJobNamedResultResponse"]:
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def get_job_errors(
        self, get_job_errors_request: "GetJobErrorsRequest"
    ) -> "GetJobErrorsResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def get_program_metadata(
        self, get_program_metadata_request: "GetProgramMetadataRequest"
    ) -> "GetProgramMetadataResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def __rpc_get_job_result_schema(
        self,
        stream: "grpclib.server.Stream[GetJobResultSchemaRequest, GetJobResultSchemaResponse]",
    ) -> None:
        request = await stream.recv_message()
        response = await self.get_job_result_schema(request)
        await stream.send_message(response)

    async def __rpc_get_job_state(
        self, stream: "grpclib.server.Stream[GetJobStateRequest, GetJobStateResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.get_job_state(request)
        await stream.send_message(response)

    async def __rpc_get_job_named_result_header(
        self,
        stream: "grpclib.server.Stream[GetJobNamedResultHeaderRequest, GetJobNamedResultHeaderResponse]",
    ) -> None:
        request = await stream.recv_message()
        response = await self.get_job_named_result_header(request)
        await stream.send_message(response)

    async def __rpc_get_job_named_result(
        self,
        stream: "grpclib.server.Stream[GetJobNamedResultRequest, GetJobNamedResultResponse]",
    ) -> None:
        request = await stream.recv_message()
        await self._call_rpc_handler_server_stream(
            self.get_job_named_result,
            stream,
            request,
        )

    async def __rpc_get_job_errors(
        self, stream: "grpclib.server.Stream[GetJobErrorsRequest, GetJobErrorsResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.get_job_errors(request)
        await stream.send_message(response)

    async def __rpc_get_program_metadata(
        self,
        stream: "grpclib.server.Stream[GetProgramMetadataRequest, GetProgramMetadataResponse]",
    ) -> None:
        request = await stream.recv_message()
        response = await self.get_program_metadata(request)
        await stream.send_message(response)

    def __mapping__(self) -> Dict[str, grpclib.const.Handler]:
        return {
            "/qm.grpc.results_analyser.JobResultsService/GetJobResultSchema": grpclib.const.Handler(
                self.__rpc_get_job_result_schema,
                grpclib.const.Cardinality.UNARY_UNARY,
                GetJobResultSchemaRequest,
                GetJobResultSchemaResponse,
            ),
            "/qm.grpc.results_analyser.JobResultsService/GetJobState": grpclib.const.Handler(
                self.__rpc_get_job_state,
                grpclib.const.Cardinality.UNARY_UNARY,
                GetJobStateRequest,
                GetJobStateResponse,
            ),
            "/qm.grpc.results_analyser.JobResultsService/GetJobNamedResultHeader": grpclib.const.Handler(
                self.__rpc_get_job_named_result_header,
                grpclib.const.Cardinality.UNARY_UNARY,
                GetJobNamedResultHeaderRequest,
                GetJobNamedResultHeaderResponse,
            ),
            "/qm.grpc.results_analyser.JobResultsService/GetJobNamedResult": grpclib.const.Handler(
                self.__rpc_get_job_named_result,
                grpclib.const.Cardinality.UNARY_STREAM,
                GetJobNamedResultRequest,
                GetJobNamedResultResponse,
            ),
            "/qm.grpc.results_analyser.JobResultsService/GetJobErrors": grpclib.const.Handler(
                self.__rpc_get_job_errors,
                grpclib.const.Cardinality.UNARY_UNARY,
                GetJobErrorsRequest,
                GetJobErrorsResponse,
            ),
            "/qm.grpc.results_analyser.JobResultsService/GetProgramMetadata": grpclib.const.Handler(
                self.__rpc_get_program_metadata,
                grpclib.const.Cardinality.UNARY_UNARY,
                GetProgramMetadataRequest,
                GetProgramMetadataResponse,
            ),
        }
