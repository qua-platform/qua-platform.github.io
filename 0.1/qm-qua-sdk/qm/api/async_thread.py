import asyncio
import logging
import pickle
import queue
import threading
import uuid
from dataclasses import dataclass, field
from typing import (
    Callable,
    Tuple,
    Any,
    Dict,
    Optional,
    AsyncIterator,
    List,
    Coroutine,
    TypeVar,
)

import betterproto
from grpclib.client import Channel
from grpclib.config import Configuration

from qm.api.models.server_details import ConnectionDetails
from qm.exceptions import QmQuaException
from qm.singleton import Singleton

logger = logging.getLogger(__name__)


class CallbackStopIteration(QmQuaException):
    def __init__(self, *args, iteration: int):
        super().__init__(*args)
        self.iteration = iteration


T = TypeVar("T")


async def async_enumerate(
    async_sequence: AsyncIterator[T], start=0
) -> AsyncIterator[Tuple[int, T]]:
    """Asynchronously enumerate an async iterator from a given start value"""
    index = start
    async for element in async_sequence:
        yield index, element
        index += 1


@dataclass(frozen=True)
class QueueMessage:
    message_id: str


@dataclass(frozen=True)
class ExecuteIteratorRequest(QueueMessage):
    function: Callable[..., AsyncIterator]
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    callback: Callable[[Any], bool] = field(default=lambda _: True)

    async def execute(self):
        async for index, value in async_enumerate(
            self.function(*self.args, **self.kwargs)
        ):
            if not self.callback(value):
                raise CallbackStopIteration(iteration=index)


@dataclass(frozen=True)
class ExecuteIterationResponse(QueueMessage):
    success: bool
    stopped_iteration: bool = field(default=False)
    iteration_num: int = field(default=-1)
    error: str = field(default="")
    pickled_exception: bytes = field(default_factory=lambda: pickle.dumps(Exception()))


@dataclass(frozen=True)
class ExecuteRequest(QueueMessage):
    function: Callable[..., Coroutine]
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

    async def execute(self):
        return await self.function(*self.args, **self.kwargs)


@dataclass(frozen=True)
class ExecuteResponse(QueueMessage):
    success: bool
    response: Optional[betterproto.Message]
    error: str = field(default="")
    pickled_exception: bytes = field(default_factory=lambda: pickle.dumps(Exception()))


@dataclass(frozen=True)
class CreateChannelRequest(QueueMessage):
    connection_details: ConnectionDetails


@dataclass(frozen=True)
class CreateChannelResponse(QueueMessage):
    channel: Channel


async def _handle_execute_request(request: ExecuteRequest) -> ExecuteResponse:
    try:
        result = await request.execute()
        return ExecuteResponse(
            success=True, response=result, message_id=request.message_id
        )
    except Exception as e:
        return ExecuteResponse(
            success=False,
            response=None,
            message_id=request.message_id,
            error=str(e),
            pickled_exception=pickle.dumps(e),
        )


async def _handle_execute_iterator_request(
    request: ExecuteIteratorRequest,
) -> ExecuteIterationResponse:
    try:
        await request.execute()
        return ExecuteIterationResponse(success=True, message_id=request.message_id)
    except CallbackStopIteration as e:
        return ExecuteIterationResponse(
            success=False,
            stopped_iteration=True,
            iteration_num=e.iteration,
            message_id=request.message_id,
        )
    except Exception as e:
        return ExecuteIterationResponse(
            success=False,
            stopped_iteration=False,
            error=str(e),
            message_id=request.message_id,
            pickled_exception=pickle.dumps(e),
        )


async def _handle_create_channel(
    request: CreateChannelRequest,
) -> CreateChannelResponse:
    connection_details = request.connection_details
    channel = Channel(
        host=connection_details.host,
        port=connection_details.port,
        ssl=connection_details.credentials is not None,
        config=Configuration(
            http2_connection_window_size=connection_details.max_message_size,
            http2_stream_window_size=connection_details.max_message_size,
        ),
    )
    return CreateChannelResponse(channel=channel, message_id=request.message_id)


QUEUE_REQUEST_MAPPING = {
    ExecuteRequest: _handle_execute_request,
    ExecuteIteratorRequest: _handle_execute_iterator_request,
    CreateChannelRequest: _handle_create_channel,
}


class AsyncThread(metaclass=Singleton):
    def __init__(self):
        self._request_queue = queue.Queue()
        self._response_queue = queue.Queue()
        self._response_event = threading.Event()

        self._exception_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._thread_init)
        self._thread.daemon = True
        self._thread.start()
        self._channels: List[Channel] = []

    def stop(self):
        for channel in self._channels:
            channel.close()
        self._stop_event.set()
        self._request_queue.put(None)
        self._thread.join()
        Singleton.delete_instances_for_type(AsyncThread)

    def create_channel(self, connection_details: ConnectionDetails) -> Channel:
        message_id = str(uuid.uuid4())
        self._request_queue.put(
            CreateChannelRequest(
                message_id=message_id, connection_details=connection_details
            )
        )
        channel = self._get_from_queue(message_id=message_id).channel
        self._channels.append(channel)
        return channel

    def execute(self, function: Callable, *args, **kwargs):
        message_id = str(uuid.uuid4())
        self._request_queue.put(
            ExecuteRequest(
                function=function, args=args, kwargs=kwargs, message_id=message_id
            )
        )
        response: ExecuteResponse = self._get_from_queue(message_id)
        if response.success:
            return response.response
        raise pickle.loads(response.pickled_exception)

    def execute_iterator(
        self, function: Callable, callback: Callable[[Any], bool], *args, **kwargs
    ):
        message_id = str(uuid.uuid4())
        self._request_queue.put(
            ExecuteIteratorRequest(
                function=function,
                args=args,
                kwargs=kwargs,
                message_id=message_id,
                callback=callback,
            )
        )
        response: ExecuteIterationResponse = self._get_from_queue(message_id)
        if not response.success and response.stopped_iteration:
            raise CallbackStopIteration(iteration=response.iteration_num)

        if not response.success and not response.stopped_iteration:
            raise pickle.loads(response.pickled_exception)

    def _get_from_queue(self, message_id: str):
        self._response_event.wait()

        if not self._exception_queue.empty():
            exc_obj = self._exception_queue.get_nowait()
            raise exc_obj

        response = self._response_queue.get_nowait()
        if response.message_id != message_id:
            logger.warning("Wrong message received")

        self._response_event.clear()
        return response

    async def _serve_loop(self):
        while not self._stop_event.is_set():
            try:
                request = self._request_queue.get(timeout=2)
                if type(request) in QUEUE_REQUEST_MAPPING:
                    response = await QUEUE_REQUEST_MAPPING[type(request)](request)
                    self._response_queue.put(response)
                    self._response_event.set()
            except queue.Empty:
                pass

    def _thread_init(self):
        try:
            asyncio.run(self._serve_loop())
        except Exception as e:
            self._exception_queue.put(e)
