from typing import Any, List, Tuple

from qm.StreamMetadata import StreamMetadataError


class QmQuaException(Exception):
    def __init__(self, message: str, *args: Any):
        self.message = message
        super().__init__(message, *args)


class QmmException(QmQuaException):
    pass


class OpenQmException(QmQuaException):
    def __init__(self, message: str, *args: Any, errors: List[Tuple[str, str, str]]):
        super().__init__(message, *args)
        self.errors = errors


class FailedToExecuteJobException(QmQuaException):
    pass


class FailedToAddJobToQueueException(QmQuaException):
    pass


class CompilationException(QmQuaException):
    pass


class JobCancelledError(QmQuaException):
    pass


class ErrorJobStateError(QmQuaException):
    def __init__(self, *args: Any, error_list: List[str]):
        super().__init__(*args)
        self._error_list = error_list if error_list else []

    def __str__(self) -> str:
        errors_string = "\n".join(error for error in self._error_list)
        return f"{super().__str__()}\n{errors_string}"


class UnknownJobStateError(QmQuaException):
    pass


class InvalidStreamMetadataError(QmQuaException):
    def __init__(self, stream_metadata_errors: List[StreamMetadataError], *args: Any):
        stream_errors_message = "\n".join(f"{e.error} at: {e.location}" for e in stream_metadata_errors)
        message = f"Error creating stream metadata:\n{stream_errors_message}"
        super().__init__(message, *args)


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
    pass


class QMTimeoutError(QmQuaException):
    pass


class QMRequestDataError(QmQuaException):
    pass


class QmServerDetectionError(QmQuaException):
    pass


class QmValueError(QmQuaException, ValueError):
    pass


class QmInvalidSchemaError(QmQuaException):
    pass


class QmInvalidResult(QmQuaException):
    pass


class QmNoResultsError(QmQuaException):
    pass
