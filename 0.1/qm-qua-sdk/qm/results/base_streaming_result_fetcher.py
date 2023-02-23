import abc
import json
import logging
import warnings
from dataclasses import dataclass
from io import BufferedWriter, BytesIO
from typing import List, Optional, Union, Tuple, Dict

import numpy
from numpy.lib import format as _format

from qm.StreamMetadata import StreamMetadataError, StreamMetadata
from qm.api.job_result_api import JobResultServiceApi
from qm.api.models.capabilities import ServerCapabilities
from qm.exceptions import InvalidStreamMetadataError
from qm.grpc.results_analyser import GetJobNamedResultResponse
from qm.persistence import BaseStore
from qm.utils import run_until_with_timeout

logger = logging.getLogger(__name__)


def _parse_dtype(simple_dtype: str) -> dict:
    def hinted_tuple_hook(obj):
        if "__tuple__" in obj:
            return tuple(obj["items"])
        else:
            return obj

    dtype = json.loads(simple_dtype, object_hook=hinted_tuple_hook)
    return dtype


@dataclass
class JobResultItemSchema:
    name: str
    dtype: dict
    shape: Tuple[int]
    is_single: bool
    expected_count: int


@dataclass
class JobResultSchema:
    items: Dict[str, JobResultItemSchema]


@dataclass
class NamedJobResultHeader:
    count_so_far: int
    is_single: bool
    output_name: str
    job_id: str
    d_type: dict
    shape: Tuple[int]
    has_dataloss: bool


@dataclass
class JobStreamingState:
    job_id: str
    done: bool
    closed: bool
    has_dataloss: bool


class BaseStreamingResultFetcher(metaclass=abc.ABCMeta):
    def __init__(
        self,
        job_id: str,
        schema: JobResultItemSchema,
        service: JobResultServiceApi,
        store: BaseStore,
        stream_metadata_errors: List[StreamMetadataError],
        stream_metadata: StreamMetadata,
        capabilities: ServerCapabilities,
    ) -> None:
        self._job_id = job_id
        self._schema = schema
        self._service = service
        self._store = store
        self._stream_metadata_errors = stream_metadata_errors
        self._stream_metadata = stream_metadata
        self._count_data_written = 0
        self._capabilities = capabilities

        self._validate_schema()

    @abc.abstractmethod
    def _validate_schema(self):
        pass

    @property
    def name(self) -> str:
        """The name of result this handle is connected to"""
        return self._schema.name

    @property
    def job_id(self) -> str:
        """The job id this result came from"""
        return self._job_id

    @property
    def expected_count(self) -> int:
        return self._schema.expected_count

    @property
    def numpy_dtype(self):
        return self._schema.dtype

    @property
    def stream_metadata(self) -> StreamMetadata:
        """Provides the StreamMetadata of this stream.

        Metadata currently includes the values and shapes of the automatically identified loops
        in the program.

        """
        if len(self._stream_metadata_errors) > 0:
            logger.error("Error creating stream metadata:")
            for x in self._stream_metadata_errors:
                logger.error(f"{x.error} in {x.location}")
            raise InvalidStreamMetadataError(self._stream_metadata_errors)
        return self._stream_metadata

    def save_to_store(
        self,
        writer: Optional[Union[BufferedWriter, BytesIO, str]] = None,
        flat_struct: bool = False,
    ) -> int:
        """Saving to persistent store the NPY data of this result handle

        Args:
            writer: An optional writer to override the store defined in
                [QuantumMachinesManager][qm.QuantumMachinesManager.QuantumMachinesManager]
            flat_struct: results will have a flat structure - dimensions
                will be part of the shape and not of the type

        Returns:
            The number of items saved
        """
        own_writer = False
        if writer is None:
            own_writer = True
            writer = self._store.job_named_result(
                self._job_id, self._schema.name
            ).for_writing()
        try:
            header = self._get_named_header(flat_struct=flat_struct)
            return self._save_to_file(header, writer)
        finally:
            if own_writer:
                writer.close()

    def wait_for_values(self, count: int = 1, timeout: Optional[float] = None):
        """Wait until we know at least `count` values were processed for this named result

        Args:
            count: The number of items to wait for
            timeout: Timeout for waiting in seconds

        Returns:

        """
        run_until_with_timeout(
            lambda: self.count_so_far() >= count,
            timeout=timeout if timeout else float("infinity"),
            timeout_message=f"result {self.name} was not done in time",
        )

    def wait_for_all_values(self, timeout: float = float("infinity")) -> bool:
        """Wait until we know all values were processed for this named result

        Args:
            timeout: Timeout for waiting in seconds

        Returns:
            True if job finished successfully and False if job has
            closed before done
        """
        if timeout is None:
            timeout = float("infinity")
            warnings.warn(
                "Parameter `timeout` can only be float since 1.1.0, please use `wait_for_all_values()` instead",
                category=DeprecationWarning,
            )

        def on_iteration() -> bool:
            header = self.get_job_state()
            return header.done or header.closed

        def on_finish() -> bool:
            header = self.get_job_state()
            return header.done

        return run_until_with_timeout(
            on_iteration_callback=on_iteration,
            on_complete_callback=on_finish,
            timeout=timeout,
            timeout_message=f"result {self.name} was not done in time",
        )

    def is_processing(self) -> bool:
        header = self.get_job_state()
        return not (header.done or header.closed)

    def count_so_far(self) -> int:
        """also `len(handle)`

        Returns:
            The number of values this result has so far
        """
        header = self._get_named_header()
        return header.count_so_far

    def __len__(self) -> int:
        return self.count_so_far()

    def has_dataloss(self) -> bool:
        """Returns:
        if there was data loss during job execution
        """
        state = self.get_job_state()
        return state.has_dataloss

    def _write_header(
        self,
        writer: Union[BufferedWriter, BytesIO, str],
        shape: Tuple[int],
        d_type: object,
    ):
        _format.write_array_header_2_0(
            writer, {"descr": d_type, "fortran_order": False, "shape": shape}
        )

    def _save_to_file(
        self, header: NamedJobResultHeader, writer: Union[BufferedWriter, BytesIO, str]
    ) -> int:
        self._count_data_written = 0
        owning_writer = False

        if type(writer) is str:
            writer = open(writer, "wb+")
            owning_writer = True

        try:
            final_shape = self._get_final_shape(header.count_so_far, header.shape)
            self._write_header(writer, final_shape, header.d_type)

            def callback(result: GetJobNamedResultResponse) -> bool:
                self._count_data_written += result.count_of_items
                writer.write(result.data)
                return True

            self._service.get_job_named_result(
                self._job_id, self.name, 0, header.count_so_far, callback=callback
            )

        finally:
            if owning_writer:
                writer.close()
        return self._count_data_written

    def get_job_state(self) -> JobStreamingState:
        if self._capabilities.has_job_streaming_state:
            response = self._service.get_job_state(self._job_id)
        else:
            response = self._service.get_named_header(self._job_id, self.name, False)
        return JobStreamingState(
            job_id=self._job_id,
            done=response.done,
            closed=response.closed,
            has_dataloss=response.has_dataloss,
        )

    def _get_named_header(
        self, check_for_errors: bool = False, flat_struct: bool = False
    ) -> NamedJobResultHeader:
        response = self._service.get_named_header(self._job_id, self.name, flat_struct)
        dtype = _parse_dtype(response.simple_d_type)

        if check_for_errors and response.has_execution_errors:
            logger.error(
                "Runtime errors were detected. Please fetch the execution report using job.execution_report() for "
                "more information"
            )

        return NamedJobResultHeader(
            count_so_far=response.count_so_far,
            is_single=response.is_single,
            output_name=self.name,
            job_id=self.job_id,
            d_type=dtype,
            shape=tuple(response.shape),
            has_dataloss=response.has_dataloss,
        )

    def fetch_all(self, *, check_for_errors: bool = False, flat_struct: bool = False):
        """Fetch a result from the current result stream saved in server memory.
        The result stream is populated by the save() and save_all() statements.
        Note that if save_all() statements are used, calling this function twice
        may give different results.

        Args:
            flat_struct: results will have a flat structure - dimensions
                will be part of the shape and not of the type

        Returns:
            all result of current result stream
        """
        return self.fetch(
            slice(0, self.count_so_far()),
            check_for_errors=check_for_errors,
            flat_struct=flat_struct,
        )

    def fetch(
        self,
        item: Union[int, slice],
        *,
        check_for_errors: bool = False,
        flat_struct: bool = False,
    ) -> numpy.array:
        """Fetch a result from the current result stream saved in server memory.
        The result stream is populated by the save() and save_all() statements.
        Note that if save_all() statements are used, calling this function twice
        with the same item index may give different results.

        Args:
            item: The index of the result in the saved results stream.
            flat_struct: results will have a flat structure - dimensions
                will be part of the shape and not of the type

        Returns:
            a single result if item is integer or multiple results if item is Python slice object.

        Example:
            ```python
            res.fetch(0)         #return the item in the top position
            res.fetch(1)         #return the item in position number 2
            res.fetch(slice(1,6))# return items from position 1 to position 6 (exclusive)
                                 # same as res.fetch_all()[1:6]
            ```
        """
        if type(item) is int:
            start = item
            stop = item + 1
            step = None
        elif type(item) is slice:
            start = item.start
            stop = item.stop
            step = item.step
        else:
            raise Exception("fetch supports only int or slice")

        if step != 1 and step is not None:
            raise Exception("fetch supports step=1 or None in slices")

        header = self._get_named_header(
            check_for_errors=check_for_errors, flat_struct=flat_struct
        )

        if stop is None:
            stop = header.count_so_far
        if start is None:
            start = 0

        writer = self._fetch_all_job_results(header, start, stop)

        if header.has_dataloss:
            logger.warning(
                f"Possible data loss detected in data for job: {self._job_id}"
            )

        return numpy.load(writer)

    def _fetch_all_job_results(self, header, start, stop):
        self._count_data_written = 0
        writer = BytesIO()
        data_writer = BytesIO()

        def callback(result: GetJobNamedResultResponse) -> bool:
            self._count_data_written += result.count_of_items
            data_writer.write(result.data)
            return True

        self._service.get_job_named_result(
            self._job_id, self._schema.name, start, stop - start, callback=callback
        )

        final_shape = self._get_final_shape(self._count_data_written, header.shape)

        self._write_header(writer, final_shape, header.d_type)

        data_writer.seek(0)
        for d in data_writer:
            writer.write(d)

        writer.seek(0)
        return writer

    @staticmethod
    def _get_final_shape(count, shape):
        if count == 1:
            final_shape = shape
        else:
            if len(shape) == 1 and shape[0] == 1:
                final_shape = (count,)
            else:
                final_shape = (count,) + shape
        return final_shape
