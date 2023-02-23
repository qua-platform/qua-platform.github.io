from io import BufferedWriter, BytesIO
from typing import List, Union, Optional

import numpy

from qm.StreamMetadata import StreamMetadataError, StreamMetadata
from qm.api.job_result_api import JobResultServiceApi
from qm.api.models.capabilities import ServerCapabilities
from qm.exceptions import QmInvalidSchemaError
from qm.persistence import BaseStore
from qm.results.base_streaming_result_fetcher import (
    BaseStreamingResultFetcher,
    JobResultItemSchema,
)

TIMESTAMPS_LEGACY_EXT = "_timestamps"


class MultipleStreamingResultFetcher(BaseStreamingResultFetcher):
    """A handle to a result of a pipeline terminating with ``save_all``"""

    def __init__(
        self,
        job_results,
        job_id: str,
        schema: JobResultItemSchema,
        service: JobResultServiceApi,
        store: BaseStore,
        stream_metadata_errors: List[StreamMetadataError],
        stream_metadata: StreamMetadata,
        capabilities: ServerCapabilities,
    ) -> None:
        self.job_results = job_results
        super().__init__(
            job_id=job_id,
            schema=schema,
            service=service,
            store=store,
            stream_metadata_errors=stream_metadata_errors,
            stream_metadata=stream_metadata,
            capabilities=capabilities,
        )

    def _validate_schema(self):
        if self._schema.is_single:
            raise QmInvalidSchemaError("expecting a multi-result schema")

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
            res.fetch(0)         # return the item in the top position
            res.fetch(1)         # return the item in position number 2
            res.fetch(slice(1,6))# return items from position 1 to position 6 (exclusive)
                                 # same as res.fetch_all()[1:6]
            ```
        """
        if flat_struct:
            return super().fetch(
                item, check_for_errors=check_for_errors, flat_struct=flat_struct
            )
        else:
            # legacy support - reconstruct the old structure
            name = self._schema.name
            timestamps_name = name + TIMESTAMPS_LEGACY_EXT
            timestamps_result_handle = self.job_results.get(timestamps_name)
            if timestamps_result_handle is None:
                return super().fetch(item, check_for_errors=check_for_errors)
            else:
                values_result = super().fetch(
                    item, check_for_errors=check_for_errors, flat_struct=True
                )

                fetched_length = len(values_result)
                if isinstance(item, slice):
                    item = slice(item.start, item.start + fetched_length, item.step)
                else:
                    item = slice(0, fetched_length)

                timestamps_result = timestamps_result_handle.fetch(
                    item, flat_struct=True, check_for_errors=check_for_errors
                )

                dtype = [
                    ("value", values_result.dtype),
                    ("timestamp", timestamps_result.dtype),
                ]  # timestamps_result.dtype.descr
                combined = numpy.rec.fromarrays(
                    [values_result, timestamps_result], dtype=dtype
                )
                return combined.view(numpy.ndarray).astype(dtype)

    def save_to_store(
        self,
        writer: Optional[Union[BufferedWriter, BytesIO, str]] = None,
        flat_struct: bool = False,
    ) -> int:
        """Saving to persistent store the NPY data of this result handle

        Args:
            writer: An optional writer to override the store defined in
                [QuantumMachinesManager][qm.QuantumMachinesManager.QuantumMachinesManager]

        Returns:
            The number of items saved
        """
        if flat_struct:
            return super().save_to_store(writer, flat_struct)
        else:
            # legacy support - reconstruct the old structure
            name = self._schema.name
            timestamps_name = name + TIMESTAMPS_LEGACY_EXT
            timestamps_result_handle = self.job_results.get(timestamps_name)
            if timestamps_result_handle is None:
                return super().save_to_store(writer, flat_struct)
            else:
                final_result = self.fetch_all(flat_struct=flat_struct)
                own_writer = False
                if writer is None:
                    own_writer = True
                    writer = self._store.job_named_result(
                        self._job_id, self._schema.name
                    ).for_writing()
                try:
                    owning_writer = False
                    if type(writer) is str:
                        writer = open(writer, "wb+")
                        owning_writer = True

                    try:
                        self._write_header(
                            writer, (len(final_result),), final_result.dtype.descr
                        )
                        writer.write(final_result.tobytes())

                    finally:
                        if owning_writer:
                            writer.close()
                    return len(final_result)
                finally:
                    if own_writer:
                        writer.close()
