from dataclasses import dataclass
from enum import Enum
from typing import List

from qm.grpc.results_analyser import GetJobErrorsResponse
from qm.api.job_result_api import JobResultServiceApi


class ExecutionErrorSeverity(Enum):
    Warn = 0
    Error = 1


@dataclass(frozen=True)
class ExecutionError:
    error_code: int
    message: str
    severity: ExecutionErrorSeverity

    def __repr__(self):
        return f"{self.error_code}\t\t{self.severity.name}\t\t{self.message}"


class ExecutionReport:
    def __init__(self, job_id: str, service: JobResultServiceApi) -> None:
        super().__init__()
        self._errors: List[ExecutionError] = []
        self._job_id: str = job_id
        self._service: JobResultServiceApi = service
        self._errors = self._load_errors()

    def _load_errors(self) -> List[ExecutionError]:
        return [
            ExecutionError(
                error_code=item.errorCode,
                message=item.message,
                severity=ExecutionReport._parse_error_severity(item.errorSeverity),
            )
            for item in self._service.get_job_errors(self._job_id)
        ]

    @staticmethod
    def _parse_error_severity(error_severity) -> ExecutionErrorSeverity:
        if error_severity == GetJobErrorsResponse.WARNING:
            return ExecutionErrorSeverity.Warn
        elif error_severity == GetJobErrorsResponse.ERROR:
            return ExecutionErrorSeverity.Error

    def has_errors(self) -> bool:
        """Returns:
        True if encountered a runtime error while executing the job.
        """
        return len(self._errors) > 0

    def errors(self) -> List[ExecutionError]:
        """Returns:
        list of all execution errors for this job
        """
        return self._errors.copy()

    def _report_header(self) -> str:
        return (
            f"Execution report for job {self._job_id}\nErrors:\n"
            f"Please refer to section: Error Indications and Error Reporting in documentation for additional information\n\n"
            "code\t\tseverity\tmessage"
        )

    def __repr__(self) -> str:
        if self.has_errors():
            errorsStr = ""
            for error in self._errors:
                errorsStr += "\n" + str(error)
            return self._report_header() + errorsStr
        else:
            return f"Execution report for job {self._job_id}\nNo errors"
