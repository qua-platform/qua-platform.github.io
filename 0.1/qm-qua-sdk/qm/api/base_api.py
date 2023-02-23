import asyncio
import functools
import logging
from typing import Callable, Any

import grpclib.exceptions
from grpclib.events import RecvInitialMetadata, listen, SendRequest

from qm.api.async_thread import AsyncThread
from qm.api.models.server_details import ConnectionDetails
from qm.exceptions import QMConnectionError, QMTimeoutError, QMRedirectionError

logger = logging.getLogger(__name__)


def connection_error_handle_decorator(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except grpclib.exceptions.GRPCError as e:
            if e.http_details.status == "302":
                raise QMRedirectionError(
                    location=e.http_details.headers.get("location")
                ) from e

            raise QMConnectionError(
                f"Encountered connection error from QOP: details: {e.message}, status: {e.status}",
                headers=e.http_details.headers,
                http_status=e.http_details.status,
            ) from e
        except asyncio.TimeoutError as e:
            raise QMTimeoutError(
                f"Timeout reached while running '{func.__name__}'"
            ) from e

    return wrapped


def connection_error_handle():
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)):
                setattr(
                    cls, attr, connection_error_handle_decorator(getattr(cls, attr))
                )
        return cls

    return decorate


class BaseApi:
    def __init__(self, connection_details: ConnectionDetails):
        self._connection_details = connection_details

        self._channel = AsyncThread().create_channel(self._connection_details)

        if self._connection_details.debug_data:
            self._create_debug_data_event()

        self._create_add_headers_event()
        self._timeout = self._connection_details.timeout

    def _create_debug_data_event(self):
        async def intercept_response(event: RecvInitialMetadata):
            metadata = event.metadata
            logger.debug(f"Collected response metadata: {metadata}")
            self._connection_details.debug_data.append(metadata)

        listen(self._channel, RecvInitialMetadata, intercept_response)

    def _create_add_headers_event(self):
        async def add_headers(event: SendRequest):
            event.metadata.update(self._connection_details.headers)

        listen(self._channel, SendRequest, add_headers)

    def _execute_on_stub(self, function: Callable, *args, **kwargs):
        return AsyncThread().execute(function, *args, **kwargs, timeout=self._timeout)

    def _execute_iterator_on_stub(
        self, function: Callable, callback: Callable[[Any], bool], *args, **kwargs
    ):
        return AsyncThread().execute_iterator(
            function, callback, *args, **kwargs, timeout=self._timeout
        )

    @property
    def channel(self):
        return self._channel

    @classmethod
    def from_api(cls, other: "BaseApi"):
        return cls(other._connection_details)
