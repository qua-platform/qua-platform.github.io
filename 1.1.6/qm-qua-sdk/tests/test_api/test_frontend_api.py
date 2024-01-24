import logging
from typing import Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
from _pytest.logging import LogCaptureFixture
from betterproto.lib.google.protobuf import Empty, StringValue

from qm.api.frontend_api import FrontendApi
from qm.api.models.compiler import CompilerOptionArguments
from qm.api.models.devices import MixerInfo
from qm.api.models.jobs import InsertDirection
from qm.api.models.quantum_machine import QuantumMachineData
from qm.api.models.server_details import ConnectionDetails
from qm.exceptions import (
    QMHealthCheckError,
    OpenQmException,
    QMFailedToGetQuantumMachineError,
    QmFailedToCloseQuantumMachineError,
    QMFailedToCloseAllQuantumMachinesError,
    FailedToAddJobToQueueException,
    CompilationException,
)
from qm.grpc.compiler import CompilerMessage
from qm.grpc.frontend import (
    HealthCheckResponse,
    ResetDataProcessingRequest,
    AddToQueueResponse,
    QueuePosition,
    AddToQueueRequest,
    AddCompiledToQueueResponse,
    ExecutionOverrides,
    AddCompiledToQueueRequest,
    CompileResponse,
    CompileRequest,
)
from qm.grpc.general_messages import ErrorMessage, MessageLevel, Matrix
from qm.grpc.qm_api import (
    HighQmApiRequest,
    HighQmApiResponse,
    HighQmApiRequestSetCorrection,
    HighQmApiRequestSetCorrectionMixerInfo,
)
from qm.grpc.qm_manager import (
    OpenQuantumMachineRequest,
    OpenQuantumMachineResponse,
    ListOpenQuantumMachinesResponse,
    ConfigValidationMessage,
    OpenQmWarning,
    PhysicalValidationMessage,
    GetQuantumMachineResponse,
    GetQuantumMachineRequest,
    CloseQuantumMachineResponse,
    CloseQuantumMachineRequest,
    CloseAllQuantumMachinesResponse,
    GetControllersResponse,
    Controller,
)
from qm.grpc.qua import QuaProgram, QuaProgramCompilerOptions
from qm.grpc.qua_config import QuaConfig


@pytest.fixture
def frontend_api() -> FrontendApi:
    connection_details = ConnectionDetails("", 0, "", "")

    frontend_api = FrontendApi(connection_details)
    frontend_api._stub = AsyncMock()

    return frontend_api


def _assert_logging_message_printed(caplog: LogCaptureFixture, message: str, level: int):
    message_to_record: Dict[str, logging.LogRecord] = {record.message: record for record in caplog.records}
    assert message in message_to_record
    assert message_to_record[message].levelno == level


def test_writing_to_file_is_not_removed_when_a_logger_added(tmp_path):
    logger = logging.getLogger("qm")
    file_path = tmp_path / "std.log"
    logger.addHandler(logging.FileHandler(filename=file_path, mode="w"))
    import qm  # This is important here to ensure the logger is initialized

    content = "This message will get logged on to a file"
    logger.warning(content)
    file_content = file_path.read_text()
    assert file_content.split("\n")[0] == content


def test_get_version(frontend_api):
    frontend_api._stub.get_version.return_value = StringValue("1.0.0")

    result = frontend_api.get_version()

    frontend_api._stub.get_version.assert_called_once_with(Empty(), timeout=frontend_api._timeout)

    assert result == "1.0.0"


def test_healthcheck(frontend_api):
    frontend_api._stub.health_check.return_value = HealthCheckResponse(
        ok=True,
        message=[""],
        warning_messages=[],
        error_messages=[],
    )

    result = frontend_api.healthcheck(strict=True)

    frontend_api._stub.health_check.assert_called_once_with(Empty(), timeout=frontend_api._timeout)

    assert result is None


def test_healthcheck_warning(frontend_api, caplog: LogCaptureFixture):
    frontend_api._stub.health_check.return_value = HealthCheckResponse(
        ok=True,
        message=[""],
        warning_messages=["warning 1", "warning 2"],
        error_messages=[],
    )

    result = frontend_api.healthcheck(strict=True)

    frontend_api._stub.health_check.assert_called_once_with(Empty(), timeout=frontend_api._timeout)
    for idx in [1, 2]:
        message = f"Health check warning: warning {idx}"
        _assert_logging_message_printed(caplog, message, logging.WARNING)

    assert result is None


def test_healthcheck_error(frontend_api, caplog: LogCaptureFixture):
    frontend_api._stub.health_check.return_value = HealthCheckResponse(
        ok=False,
        message=["error message"],
        warning_messages=[],
        error_messages=["error 1", "error 2"],
    )
    with pytest.raises(QMHealthCheckError, match="Health check failed"):
        frontend_api.healthcheck(strict=True)

    frontend_api._stub.health_check.assert_called_once_with(Empty(), timeout=frontend_api._timeout)
    for idx in [1, 2]:
        message = f"Health check error: error {idx}"
        _assert_logging_message_printed(caplog, message, logging.ERROR)


def test_healthcheck_non_strict(frontend_api):
    # Set up the mock
    frontend_api._stub.health_check.return_value = HealthCheckResponse(
        ok=False,
        message=["error message"],
        warning_messages=[],
        error_messages=["error 1", "error 2"],
    )

    result = frontend_api.healthcheck(strict=False)

    frontend_api._stub.health_check.assert_called_once_with(Empty(), timeout=frontend_api._timeout)

    assert result is None


def test_reset_data_processing(frontend_api):
    frontend_api._stub.reset_data_processing.return_value = Empty()

    frontend_api.reset_data_processing()

    frontend_api._stub.reset_data_processing.assert_called_once_with(
        ResetDataProcessingRequest(), timeout=frontend_api._timeout
    )


def test_open_qm(frontend_api):
    frontend_api._stub.open_quantum_machine.return_value = OpenQuantumMachineResponse(
        success=True,
        machine_id="qm_123",
        open_qm_warnings=[],
        config_validation_errors=[],
        physical_validation_errors=[],
    )

    result = frontend_api.open_qm(QuaConfig(), close_other_machines=True)

    frontend_api._stub.open_quantum_machine.assert_called_once_with(
        OpenQuantumMachineRequest(config=QuaConfig(), always=True), timeout=frontend_api._timeout
    )

    assert result == "qm_123"


def test_list_open_quantum_machines(frontend_api):
    frontend_api._stub.list_open_quantum_machines.return_value = ListOpenQuantumMachinesResponse(
        machine_i_ds=["m1", "m2", "m3"]
    )

    result = frontend_api.list_open_quantum_machines()
    frontend_api._stub.list_open_quantum_machines.assert_called_once_with(Empty(), timeout=frontend_api._timeout)
    assert result == ["m1", "m2", "m3"]


def test_open_qm_success(frontend_api):
    frontend_api._stub.open_quantum_machine.return_value = OpenQuantumMachineResponse(
        success=True,
        machine_id="qm_123",
        open_qm_warnings=[],
        config_validation_errors=[],
        physical_validation_errors=[],
    )

    result = frontend_api.open_qm(QuaConfig(), close_other_machines=True)

    frontend_api._stub.open_quantum_machine.assert_called_once_with(
        OpenQuantumMachineRequest(config=QuaConfig(), always=True), timeout=frontend_api._timeout
    )

    assert result == "qm_123"


def test_open_qm_warnings(frontend_api, caplog: LogCaptureFixture):
    frontend_api._logger = MagicMock()
    frontend_api._stub.open_quantum_machine.return_value = OpenQuantumMachineResponse(
        success=True,
        machine_id="qm_123",
        open_qm_warnings=[
            OpenQmWarning(code=1, message="warning 1"),
            OpenQmWarning(code=2, message="warning 2"),
        ],
        config_validation_errors=[],
        physical_validation_errors=[],
    )

    result = frontend_api.open_qm(QuaConfig(), close_other_machines=True)

    frontend_api._stub.open_quantum_machine.assert_called_once_with(
        OpenQuantumMachineRequest(config=QuaConfig(), always=True), timeout=frontend_api._timeout
    )

    for idx in [1, 2]:
        message = f"Open QM ended with warning {idx}: warning {idx}"
        _assert_logging_message_printed(caplog, message, logging.WARNING)

    assert result == "qm_123"


def test_open_qm_config_errors(frontend_api):
    frontend_api._stub.open_quantum_machine.return_value = OpenQuantumMachineResponse(
        success=False,
        machine_id="",
        open_qm_warnings=[],
        config_validation_errors=[
            ConfigValidationMessage(path="path", group="group", message="error message"),
        ],
        physical_validation_errors=[],
    )

    with pytest.raises(OpenQmException):
        frontend_api.open_qm(QuaConfig(), close_other_machines=True)

    frontend_api._stub.open_quantum_machine.assert_called_once_with(
        OpenQuantumMachineRequest(config=QuaConfig(), always=True), timeout=frontend_api._timeout
    )


def test_open_qm_physical_errors(frontend_api):
    frontend_api._stub.open_quantum_machine.return_value = OpenQuantumMachineResponse(
        success=False,
        machine_id="",
        open_qm_warnings=[],
        config_validation_errors=[],
        physical_validation_errors=[
            PhysicalValidationMessage(path="path", group="group", message="error message"),
        ],
    )

    with pytest.raises(OpenQmException):
        frontend_api.open_qm(QuaConfig(), close_other_machines=True)

    # Ensure the function was called correctly
    frontend_api._stub.open_quantum_machine.assert_called_once_with(
        OpenQuantumMachineRequest(config=QuaConfig(), always=True), timeout=frontend_api._timeout
    )


def test_get_quantum_machine_success(frontend_api):
    config = QuaConfig()
    frontend_api._stub.get_quantum_machine.return_value = GetQuantumMachineResponse(
        success=True,
        machine_id="qm_123",
        config=config,
        errors=[],
    )

    result = frontend_api.get_quantum_machine("qm_123")

    frontend_api._stub.get_quantum_machine.assert_called_once_with(
        GetQuantumMachineRequest(machine_id="qm_123"), timeout=frontend_api._timeout
    )

    assert result == QuantumMachineData(machine_id="qm_123", config=config)


def test_get_quantum_machine_failure(frontend_api):
    frontend_api._stub.get_quantum_machine.return_value = GetQuantumMachineResponse(
        success=False,
        machine_id="",
        config=None,
        errors=[
            ErrorMessage(message="error message 1"),
            ErrorMessage(message="error message 2"),
        ],
    )

    with pytest.raises(QMFailedToGetQuantumMachineError):
        frontend_api.get_quantum_machine("qm_123")

    frontend_api._stub.get_quantum_machine.assert_called_once_with(
        GetQuantumMachineRequest(machine_id="qm_123"), timeout=frontend_api._timeout
    )


def test_close_quantum_machine_success(frontend_api):
    frontend_api._stub.close_quantum_machine.return_value = CloseQuantumMachineResponse(success=True, errors=[])

    result = frontend_api.close_quantum_machine("qm_123")

    frontend_api._stub.close_quantum_machine.assert_called_once_with(
        CloseQuantumMachineRequest(machine_id="qm_123"), timeout=frontend_api._timeout
    )

    assert result is True


def test_close_quantum_machine_failure(frontend_api):
    frontend_api._stub.close_quantum_machine.return_value = CloseQuantumMachineResponse(
        success=False,
        errors=[
            ErrorMessage(message="error message 1"),
            ErrorMessage(message="error message 2"),
        ],
    )

    with pytest.raises(QmFailedToCloseQuantumMachineError):
        frontend_api.close_quantum_machine("qm_123")

    frontend_api._stub.close_quantum_machine.assert_called_once_with(
        CloseQuantumMachineRequest(machine_id="qm_123"), timeout=frontend_api._timeout
    )


def test_close_all_quantum_machines_success(frontend_api):
    frontend_api._stub.close_all_quantum_machines.return_value = CloseAllQuantumMachinesResponse(
        success=True, errors=[]
    )

    frontend_api.close_all_quantum_machines()

    frontend_api._stub.close_all_quantum_machines.assert_called_once_with(Empty(), timeout=frontend_api._timeout)


def test_close_all_quantum_machines_failure(frontend_api):
    frontend_api._stub.close_all_quantum_machines.return_value = CloseAllQuantumMachinesResponse(
        success=False,
        errors=[
            ErrorMessage(message="error message 1"),
            ErrorMessage(message="error message 2"),
        ],
    )

    with pytest.raises(QMFailedToCloseAllQuantumMachinesError):
        frontend_api.close_all_quantum_machines()

    frontend_api._stub.close_all_quantum_machines.assert_called_once_with(Empty(), timeout=frontend_api._timeout)


def test_get_controllers(frontend_api):
    frontend_api._stub.get_controllers.return_value = GetControllersResponse(
        controllers=[
            Controller(name="controller 1"),
            Controller(name="controller 2"),
        ]
    )

    result = frontend_api.get_controllers()

    frontend_api._stub.get_controllers.assert_called_once_with(Empty(), timeout=frontend_api._timeout)

    assert result == [
        Controller(name="controller 1"),
        Controller(name="controller 2"),
    ]


def test_clear_all_job_results(frontend_api):
    frontend_api.clear_all_job_results()

    frontend_api._stub.clear_all_job_results.assert_called_once_with(Empty(), timeout=frontend_api._timeout)


def test_add_to_queue_success(frontend_api, caplog: LogCaptureFixture):
    frontend_api._stub.add_to_queue.return_value = AddToQueueResponse(
        ok=True,
        job_id="job_1",
        messages=[
            CompilerMessage(level=MessageLevel.Message_LEVEL_INFO, message="info message"),
            CompilerMessage(level=MessageLevel.Message_LEVEL_WARNING, message="warning message"),
            CompilerMessage(level=MessageLevel.Message_LEVEL_ERROR, message="error message"),
        ],
    )

    result = frontend_api.add_to_queue(
        machine_id="machine_1",
        program=QuaProgram(),
        compiler_options=CompilerOptionArguments(),
        insert_direction=InsertDirection.end,
    )

    frontend_api._stub.add_to_queue.assert_called_once_with(
        AddToQueueRequest(
            quantum_machine_id="machine_1",
            high_level_program=QuaProgram(compiler_options=QuaProgramCompilerOptions(flags=[])),
            queue_position=QueuePosition(end=Empty()),
        ),
        timeout=None,
    )

    assert result == "job_1"

    _assert_logging_message_printed(caplog, "Sending program to QOP for compilation", logging.INFO)
    _assert_logging_message_printed(caplog, "info message", logging.INFO)
    _assert_logging_message_printed(caplog, "warning message", logging.WARNING)
    _assert_logging_message_printed(caplog, "error message", logging.ERROR)


def test_add_to_queue_failure(frontend_api, caplog: LogCaptureFixture):
    frontend_api._stub.add_to_queue.return_value = AddToQueueResponse(
        ok=False,
        job_id="job_1",
        messages=[CompilerMessage(level=MessageLevel.Message_LEVEL_ERROR, message="error message")],
    )

    with pytest.raises(FailedToAddJobToQueueException, match="Job job_1 failed. Failed to execute program."):
        frontend_api.add_to_queue(
            machine_id="machine_1",
            program=QuaProgram(),
            compiler_options=CompilerOptionArguments(),
            insert_direction=InsertDirection.end,
        )

    frontend_api._stub.add_to_queue.assert_called_once_with(
        AddToQueueRequest(
            quantum_machine_id="machine_1",
            high_level_program=QuaProgram(compiler_options=QuaProgramCompilerOptions(flags=[])),
            queue_position=QueuePosition(end=Empty()),
        ),
        timeout=None,
    )

    _assert_logging_message_printed(caplog, "Job job_1 failed. Failed to execute program.", logging.ERROR)


def test_add_compiled_to_queue_success(frontend_api, caplog: LogCaptureFixture):
    frontend_api._stub.add_compiled_to_queue.return_value = AddCompiledToQueueResponse(
        ok=True,
        job_id="job_1",
        errors=[],
    )

    result = frontend_api.add_compiled_to_queue(
        machine_id="machine_1",
        program_id="program_1",
        execution_overrides=ExecutionOverrides(),
    )

    frontend_api._stub.add_compiled_to_queue.assert_called_once_with(
        AddCompiledToQueueRequest(
            quantum_machine_id="machine_1",
            program_id="program_1",
            queue_position=QueuePosition(end=Empty()),
            execution_overrides=ExecutionOverrides(),
        ),
        timeout=frontend_api._timeout,
    )

    assert result == "job_1"
    erroneous_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert not erroneous_records


def test_add_compiled_to_queue_failure(frontend_api, caplog: LogCaptureFixture):
    frontend_api._stub.add_compiled_to_queue.return_value = AddCompiledToQueueResponse(
        ok=False,
        job_id="job_1",
        errors=[
            ErrorMessage(message="error message"),
        ],
    )

    with pytest.raises(FailedToAddJobToQueueException, match="Job job_1 failed. Failed to execute program."):
        frontend_api.add_compiled_to_queue(
            machine_id="machine_1",
            program_id="program_1",
            execution_overrides=ExecutionOverrides(),
        )

    frontend_api._stub.add_compiled_to_queue.assert_called_once_with(
        AddCompiledToQueueRequest(
            quantum_machine_id="machine_1",
            program_id="program_1",
            queue_position=QueuePosition(end=Empty()),
            execution_overrides=ExecutionOverrides(),
        ),
        timeout=frontend_api._timeout,
    )

    _assert_logging_message_printed(caplog, "error message", logging.ERROR)
    _assert_logging_message_printed(caplog, "Job job_1 failed. Failed to execute program.", logging.ERROR)


def test_compiled_success(frontend_api, caplog: LogCaptureFixture):
    frontend_api._stub.compile.return_value = CompileResponse(
        ok=True,
        program_id="prog_1",
        messages=[
            CompilerMessage(level=MessageLevel.Message_LEVEL_INFO, message="info message"),
            CompilerMessage(level=MessageLevel.Message_LEVEL_WARNING, message="warning message"),
            CompilerMessage(level=MessageLevel.Message_LEVEL_ERROR, message="error message"),
        ],
    )

    result = frontend_api.compile(
        machine_id="machine_1", program=QuaProgram(), compiler_options=CompilerOptionArguments(flags=["flag1"])
    )

    frontend_api._stub.compile.assert_called_once_with(
        CompileRequest(
            quantum_machine_id="machine_1",
            high_level_program=QuaProgram(compiler_options=QuaProgramCompilerOptions(flags=["flag1"])),
        ),
        timeout=None,
    )

    assert result == "prog_1"

    _assert_logging_message_printed(caplog, "info message", logging.INFO)
    _assert_logging_message_printed(caplog, "warning message", logging.WARNING)
    _assert_logging_message_printed(caplog, "error message", logging.ERROR)


def test_compile_errors(frontend_api, caplog: LogCaptureFixture):
    frontend_api._stub.compile.return_value = CompileResponse(
        ok=False,
        program_id="prog_1",
        messages=[],
    )

    with pytest.raises(CompilationException, match="Compilation of program prog_1 failed"):
        frontend_api.compile(
            machine_id="machine_1", program=QuaProgram(), compiler_options=CompilerOptionArguments(flags=["flag1"])
        )

    frontend_api._stub.compile.assert_called_once_with(
        CompileRequest(
            quantum_machine_id="machine_1",
            high_level_program=QuaProgram(compiler_options=QuaProgramCompilerOptions(flags=["flag1"])),
        ),
        timeout=None,
    )

    _assert_logging_message_printed(caplog, "Compilation of program prog_1 failed", logging.ERROR)


def test_set_correction(frontend_api, ignore_deprecation):
    frontend_api._stub.compile.return_value = HighQmApiResponse(ok=True, errors=[])

    frontend_api.set_correction(
        "machine 1",
        MixerInfo(
            "m1",
            False,
            lo_frequency_double=0.0,
            intermediate_frequency_double=1.1,
            lo_frequency=1,
            intermediate_frequency=2,
        ),
        Matrix(1.0, 0.0, 0.0, 1.0),
    )

    frontend_api._stub.perform_qm_request.assert_called_with(
        HighQmApiRequest(
            set_correction=HighQmApiRequestSetCorrection(
                mixer=HighQmApiRequestSetCorrectionMixerInfo(
                    **MixerInfo(
                        "m1",
                        False,
                        lo_frequency_double=0.0,
                        intermediate_frequency_double=1.1,
                        lo_frequency=1,
                        intermediate_frequency=2,
                    ).as_dict()
                ),
                correction=Matrix(1.0, 0.0, 0.0, 1.0),
            ),
            quantum_machine_id="machine 1",
        ),
        timeout=frontend_api._timeout,
    )
