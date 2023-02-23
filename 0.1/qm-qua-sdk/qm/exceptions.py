import re
from typing import List, Dict


class QmQuaException(Exception):
    pass


class QmmException(QmQuaException):
    pass


class OpenQmException(QmQuaException):
    pass


class FailedToExecuteJobException(QmQuaException):
    pass


class FailedToAddJobToQueueException(QmQuaException):
    pass


class CompilationException(QmQuaException):
    pass


class JobCancelledError(QmQuaException):
    pass


class ErrorJobStateError(QmQuaException):
    def __init__(self, *args, error_list: List[str]):
        super().__init__(*args)
        self._error_list = error_list if error_list else []

    def __str__(self):
        errors_string = "\n".join(error for error in self._error_list)
        return f"{super().__str__()}\n{errors_string}"


class UnknownJobStateError(QmQuaException):
    pass


class InvalidStreamMetadataError(QmQuaException):
    pass


class ConfigValidationException(QmQuaException):
    pass


class ConfigSerializationException(QmQuaException):
    pass


class UnsupportedCapabilityError(QmQuaException):
    pass


class InvalidConfigError(QmQuaException):
    pass


class QMHealthCheckError(QmQuaException):
    pass


class QMFailedToGetQuantumMachineError(QmQuaException):
    pass


class QMSimulationError(QmQuaException):
    pass


class QmFailedToCloseQuantumMachineError(QmQuaException):
    pass


class QMFailedToCloseAllQuantumMachinesError(QmFailedToCloseQuantumMachineError):
    pass


class QMRequestError(QmQuaException):
    pass


class QMConnectionError(QmQuaException):
    def __init__(self, *args, headers: Dict[str, str] = None, http_status: str = None):
        super().__init__(*args)
        self.headers = headers
        self.http_status = http_status


class QMRedirectionError(QmQuaException):
    def __init__(self, *args, location: str):
        super().__init__(*args)
        self.host = None
        self.port = None
        self.location = location

        match = re.match("(?P<host>[^:]*):(?P<port>[0-9]*)(/(?P<url>.*))?", location)
        if match:
            host, port, _, __ = match.groups()


class QMTimeoutError(QmQuaException):
    pass


class QMRequestDataError(QmQuaException):
    pass


class QmServerDetectionError(QmQuaException):
    pass


class QmValueError(QmQuaException):
    pass


class QmInvalidSchemaError(QmQuaException):
    pass


class QmInvalidResult(QmQuaException):
    pass
