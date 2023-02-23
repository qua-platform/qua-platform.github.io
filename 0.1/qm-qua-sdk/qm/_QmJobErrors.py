from typing import Tuple

from qm.grpc.errors import (
    JobManagerErrorTypes,
    JobOperationSpecificErrorTypes,
    ConfigQueryErrorTypes,
)
from qm.grpc.job_manager import JobManagerResponseHeader


class QmApiError(BaseException):
    def __init__(self, code: int, message: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class UnspecifiedError(QmApiError):
    def __init__(self, message: str) -> None:
        super().__init__(0, message)


class _QmJobError(QmApiError):
    """Base class for exceptions in this module."""

    pass


class MissingJobError(_QmJobError):
    """if the job isn't recognized by the server (can happen if it never ran or if it was already deleted)"""

    def __init__(self) -> None:
        super().__init__(1000)


class InvalidJobExecutionStatusError(_QmJobError):
    def __init__(self) -> None:
        super().__init__(1001)


class InvalidOperationOnSimulatorJobError(_QmJobError):
    def __init__(self) -> None:
        super().__init__(1002)


class InvalidOperationOnRealJobError(_QmJobError):
    def __init__(self) -> None:
        super().__init__(1003)


class UnknownInputStreamError(_QmJobError):
    def __init__(self) -> None:
        super().__init__(1006)


class ConfigQueryError(QmApiError):
    pass


class MissingElementError(ConfigQueryError):
    """"""

    @staticmethod
    def _build_from_response(request, response) -> "MissingElementError":
        return MissingElementError(
            response.job_manager_response_header.job_error_details.message
        )

    def __init__(self, message: str):
        super().__init__(4001, message)


class MissingDigitalInputError(ConfigQueryError):
    """"""

    @staticmethod
    def _build_from_response(request, response) -> "MissingDigitalInputError":
        return MissingDigitalInputError(
            response.job_manager_response_header.job_error_details.message
        )

    def __init__(self, message: str):
        super().__init__(4002, message)


class _InvalidConfigChangeError(QmApiError):
    pass


class ElementWithSingleInputError(_InvalidConfigChangeError):
    @staticmethod
    def _build_from_response(request, response) -> "ElementWithSingleInputError":
        return ElementWithSingleInputError(request.qe_name)

    def __init__(self, element_name: str):
        super().__init__(3000)
        self.element_name = element_name


class InvalidElementCorrectionError(_InvalidConfigChangeError):
    """If the correction values are invalid"""

    @staticmethod
    def _build_from_response(request, response) -> "InvalidElementCorrectionError":
        return InvalidElementCorrectionError(
            response.job_manager_response_header.job_error_details.message,
            request.qe_name,
            (
                request.correction.v00,
                request.correction.v01,
                request.correction.v10,
                request.correction.v11,
            ),
        )

    def __init__(
        self,
        message: str,
        element_name: str,
        correction: Tuple[float, float, float, float],
    ) -> None:
        super().__init__(3001, message)
        self.element_name = element_name
        self.correction = correction


class ElementWithoutIntermediateFrequencyError(_InvalidConfigChangeError):
    @staticmethod
    def _build_from_response(
        request, response
    ) -> "ElementWithoutIntermediateFrequencyError":
        return ElementWithoutIntermediateFrequencyError(request.qe_name)

    def __init__(self, element_name: str):
        super().__init__(3002)
        self.element_name = element_name


class InvalidDigitalInputThresholdError(_InvalidConfigChangeError):
    @staticmethod
    def _build_from_response(request, response) -> "InvalidDigitalInputThresholdError":
        return InvalidDigitalInputThresholdError(
            response.job_manager_response_header.job_error_details.message
        )

    def __init__(self, message: str):
        super().__init__(3003)
        self.message = message


class InvalidDigitalInputDeadtimeError(_InvalidConfigChangeError):
    @staticmethod
    def _build_from_response(request, response) -> "InvalidDigitalInputDeadtimeError":
        return InvalidDigitalInputDeadtimeError(
            response.job_manager_response_header.job_error_details.message
        )

    def __init__(self, message: str):
        super().__init__(3004)
        self.message = message


class InvalidDigitalInputPolarityError(_InvalidConfigChangeError):
    @staticmethod
    def _build_from_response(request, response) -> "InvalidDigitalInputPolarityError":
        return InvalidDigitalInputPolarityError(
            response.job_manager_response_header.job_error_details.message
        )

    def __init__(self, message: str):
        super().__init__(3005)
        self.message = message


def _handle_job_manager_error(request, response, valid_errors):
    api_response: JobManagerResponseHeader = response.job_manager_response_header
    if not api_response.success:
        error_type = api_response.job_manager_error_type

        if error_type == JobManagerErrorTypes.MissingJobError:
            raise MissingJobError()
        elif error_type == JobManagerErrorTypes.InvalidJobExecutionStatusError:
            raise InvalidJobExecutionStatusError()
        elif error_type == JobManagerErrorTypes.InvalidOperationOnSimulatorJobError:
            raise InvalidOperationOnSimulatorJobError()
        elif error_type == JobManagerErrorTypes.InvalidOperationOnRealJobError:
            raise InvalidOperationOnRealJobError()
        elif error_type == JobManagerErrorTypes.JobOperationSpecificError:
            exception_to_raise = _get_handle_job_operation_error(request, response)
            if (
                exception_to_raise is not None
                and type(exception_to_raise) in valid_errors
            ):
                raise exception_to_raise
            else:
                raise UnspecifiedError("Unspecified operation specific error")
        elif error_type == JobManagerErrorTypes.ConfigQueryError:
            exception_to_raise = _get_handle_config_query_error(request, response)
            if (
                exception_to_raise is not None
                and type(exception_to_raise) in valid_errors
            ):
                raise exception_to_raise
            else:
                raise UnspecifiedError("Unspecified operation specific error")
        elif error_type == JobManagerErrorTypes.UnknownInputStreamError:
            raise UnknownInputStreamError()
        else:
            raise UnspecifiedError("Unspecified operation error")


def _get_handle_config_query_error(request, response):
    error_type = (
        response.job_manager_response_header.job_error_details.config_query_error_type
    )
    exception_to_raise = None
    if error_type == ConfigQueryErrorTypes.MissingElementError:
        exception_to_raise = MissingElementError._build_from_response(request, response)
    elif error_type == ConfigQueryErrorTypes.MissingDigitalInputError:
        exception_to_raise = MissingDigitalInputError._build_from_response(
            request, response
        )
    else:
        exception_to_raise = UnspecifiedError("Unspecified config query error")

    return exception_to_raise


def _get_handle_job_operation_error(request, response):
    error_type = (
        response.job_manager_response_header.job_error_details.job_operation_specific_error_type
    )

    if error_type == JobOperationSpecificErrorTypes.SingleInputElementError:
        exception_to_raise = ElementWithSingleInputError._build_from_response(
            request, response
        )
    elif error_type == JobOperationSpecificErrorTypes.InvalidCorrectionMatrixError:
        exception_to_raise = InvalidElementCorrectionError._build_from_response(
            request, response
        )
    elif (
        error_type
        == JobOperationSpecificErrorTypes.ElementWithoutIntermediateFrequencyError
    ):
        exception_to_raise = (
            ElementWithoutIntermediateFrequencyError._build_from_response(
                request, response
            )
        )
    elif error_type == JobOperationSpecificErrorTypes.InvalidDigitalInputThresholdError:
        exception_to_raise = InvalidDigitalInputThresholdError._build_from_response(
            request, response
        )
    elif error_type == JobOperationSpecificErrorTypes.InvalidDigitalInputDeadtimeError:
        exception_to_raise = InvalidDigitalInputDeadtimeError._build_from_response(
            request, response
        )
    elif error_type == JobOperationSpecificErrorTypes.InvalidDigitalInputPolarityError:
        exception_to_raise = InvalidDigitalInputPolarityError._build_from_response(
            request, response
        )
    else:
        exception_to_raise = UnspecifiedError("Unspecified operation specific error")

    return exception_to_raise
