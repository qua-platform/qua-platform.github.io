import asyncio
from dataclasses import dataclass
from typing import List
from unittest.mock import patch
import grpclib
import pytest
from grpclib import Status
from qm.api.base_api import connection_error_handle_decorator
import logging


@dataclass
class TestArgs:
    error: Exception
    is_debug: bool
    logger_exception_called: bool


test_args: List[TestArgs] = [
    TestArgs(error=grpclib.exceptions.GRPCError(status=Status.UNKNOWN), is_debug=True, logger_exception_called=True),
    TestArgs(error=grpclib.exceptions.GRPCError(status=Status.UNKNOWN), is_debug=False, logger_exception_called=False),
    TestArgs(error=asyncio.TimeoutError(), is_debug=True, logger_exception_called=True),
    TestArgs(error=asyncio.TimeoutError(), is_debug=False, logger_exception_called=False),
    TestArgs(error=Exception(), is_debug=True, logger_exception_called=False),
    TestArgs(error=Exception(), is_debug=False, logger_exception_called=False),
]


@pytest.mark.parametrize("args", test_args)
def test_connection_error_handle_decorator(args: TestArgs):
    def mock_method(_args, _kwargs):
        raise args.error

    with patch('logging.getLogger') as logger_mock:
        logger_mock.return_value = type('', (), {'level': logging.DEBUG if args.is_debug else logging.INFO})()
        with patch('logging.Logger.exception') as logger_exception_mock:
            try:
                connection_error_handle_decorator(mock_method)(None, None)
            except:
                pass

    assert logger_exception_mock.called == args.logger_exception_called
