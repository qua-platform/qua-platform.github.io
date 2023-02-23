import logging
from typing import Optional, Union

from qm.exceptions import QmInvalidSchemaError
from qm.results.base_streaming_result_fetcher import BaseStreamingResultFetcher

logger = logging.getLogger(__name__)


class SingleStreamingResultFetcher(BaseStreamingResultFetcher):
    """A handle to a result of a pipeline terminating with ``save``"""

    def _validate_schema(self):
        if not self._schema.is_single:
            raise QmInvalidSchemaError("expecting a single-result schema")

    def wait_for_values(self, count: int = 1, timeout: Optional[float] = None):
        if count != 1:
            raise RuntimeError("single result can wait only for a single value")
        return super().wait_for_values(1, timeout)

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
        return self.fetch(0, flat_struct=flat_struct, check_for_errors=check_for_errors)

    def fetch(
        self,
        item: Union[int, slice],
        *,
        check_for_errors: bool = False,
        flat_struct: bool = False,
    ):

        """Fetch a single result from the current result stream saved in server memory.
        The result stream is populated by the save().

        Args:
            item: ignored
            flat_struct: results will have a flat structure - dimensions
                will be part of the shape and not of the type

        Returns:
            the current result

        Example:
            ```python
            res.fetch() # return the item in the top position
            ```
        """
        if (isinstance(item, int) and item != 0) or isinstance(item, slice):
            logger.warning("Fetching single result will always return the single value")
        value = super().fetch(
            0, check_for_errors=check_for_errors, flat_struct=flat_struct
        )
        if flat_struct:
            if len(value) == 0:
                return None
            elif len(value) == 1:
                return value[0]
            else:
                return value
        else:
            if len(value) == 0:
                return None
            elif len(value[0]) == 1:
                return value[0][0]
            else:
                return value[0]
