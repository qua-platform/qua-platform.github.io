import datetime

from betterproto import StringValue
from betterproto.lib.google.protobuf import Struct

from qm.grpc.compiler import ValidationResponse
from qm.grpc.frontend import (
    HealthCheckResponse,
    ExecutionResponse,
    SimulatedResponsePart,
    AddToQueueResponse,
    CompileResponse,
    AddCompiledToQueueResponse,
    RemovePendingJobsResponse,
    GetPendingJobsResponse,
    JobExecutionStatusPending,
    JobExecutionStatusRunning,
    GetJobExecutionStatusResponse,
    JobExecutionStatus,
    PausedStatusResponse,
    ResumeResponse,
    HaltResponse,
    ResetDataProcessingResponse,
    QmDataResponse,
    IsJobRunningResponse,
    SimulationResponse,
    PerformHalDebugCommandResponse,
    GetSimulatedQuantumStateResponse,
    IsJobAcquiringDataResponse,
)
from qm.grpc.qm_api import HighQmApiResponse
from qm.grpc.qm_manager import (
    OpenQuantumMachineResponse,
    CloseQuantumMachineResponse,
    GetQuantumMachineResponse,
    GetRunningJobResponse,
    ListOpenQuantumMachinesResponse,
    CloseAllQuantumMachinesResponse,
    GetControllersResponse,
)
from qm.grpc.results_analyser import SimulatorSamplesResponse
from benchmark.config import MOCK_CONFIG_PB

MOCK_MACHINE_ID = "mock-qm"
MOCK_JOB_ID = "mock-job"
MOCK_PROGRAM_ID = "mock-program"
MOCK_VERSION = "1.3.3.7"

MOCK_SIMULATED_RESPONSE_PART = SimulatedResponsePart(
    analog_outputs=Struct(), digital_outputs=Struct(), waveform_report=Struct(), errors=[]
)
MOCK_JOB_EXECUTION_STATUS_PENDING = JobExecutionStatusPending(
    position_in_queue=1, time_added=datetime.datetime.now(), added_by="mock"
)
MOCK_JOB_EXECUTION_STATUS_RUNNING = JobExecutionStatusRunning(
    time_added=datetime.datetime.now(), added_by="mock", time_started=datetime.datetime.now()
)

BASE_JOB_EXECUTION_STATUS = JobExecutionStatus(running=MOCK_JOB_EXECUTION_STATUS_RUNNING)
BASE_GET_VERSION_RESPONSE = StringValue("1.3.3.7")
BASE_HEALTH_CHECK_RESPONSE = HealthCheckResponse(ok=True)
BASE_EXECUTION_RESPONSE = ExecutionResponse(
    ok=True,
    job_id=MOCK_JOB_ID,
    messages=[],
    metadata="random",
    simulated=MOCK_SIMULATED_RESPONSE_PART,
    config=MOCK_CONFIG_PB,
)
BASE_ADD_TO_QUEUE_RESPONSE = AddToQueueResponse(ok=True, job_id=MOCK_JOB_ID, messages=[])
BASE_COMPILE_RESPONSE = CompileResponse(ok=True, program_id=MOCK_PROGRAM_ID, messages=[])
BASE_ADD_COMPILED_TO_QUEUE_RESPONSE = AddCompiledToQueueResponse(ok=True, job_id=MOCK_JOB_ID, errors=[])
BASE_REMOVE_PENDING_JOBS_RESPONSE = RemovePendingJobsResponse(numbers_of_jobs_removed=1)
BASE_GET_PENDING_JOBS_RESPONSE = GetPendingJobsResponse(pending_jobs={MOCK_JOB_ID: MOCK_JOB_EXECUTION_STATUS_PENDING})
BASE_GET_JOB_EXECUTION_STATUS_RESPONSE = GetJobExecutionStatusResponse(status=BASE_JOB_EXECUTION_STATUS)
BASE_GET_PAUSED_STATUS_RESPONSE = PausedStatusResponse()
BASE_RESUME_RESPONSE = ResumeResponse()
BASE_HALT_STATUS = HaltResponse()
BASE_RESET_DATA_PROCESSING_RESPONSE = ResetDataProcessingResponse()
BASE_VALIDATION_CONFIG_RESPONSE = ValidationResponse()
BASE_PERFORM_QM_REQUEST_RESPONSE = HighQmApiResponse()
BASE_REQUEST_DATA_RESPONSE = QmDataResponse()
BASE_PULL_SIMULATOR_SAMPLES_RESPONSE = SimulatorSamplesResponse()
BASE_OPEN_QUANTUM_MACHINE_RESPONSE = OpenQuantumMachineResponse(machine_id=MOCK_MACHINE_ID, success=True)
BASE_CLOSE_QUANTUM_MACHINE_RESPONSE = CloseQuantumMachineResponse()
BASE_GET_QUANTUM_MACHINE_RESPONSE = GetQuantumMachineResponse()
BASE_GET_RUNNING_JOB_RESPONSE = GetRunningJobResponse()
BASE_LIST_OPEN_QUANTUM_MACHINES_RESPONSE = ListOpenQuantumMachinesResponse()
BASE_CLOSE_ALL_QUANTUM_MACHINES_RESPONSE = CloseAllQuantumMachinesResponse()
BASE_GET_CONTROLLERS_RESPONSE = GetControllersResponse()
BASE_IS_JOB_RUNNING_RESPONSE = IsJobRunningResponse()
BASE_IS_JOB_ACQUIRING_DATA_RESPONSE = IsJobAcquiringDataResponse()
BASE_SIMULATE_RESPONSE = SimulationResponse()
BASE_PERFORM_HAL_DEBUG_COMMAND_RESPONSE = PerformHalDebugCommandResponse()
BASE_GET_SIMULATED_QUANTUM_STATE_RESPONSE = GetSimulatedQuantumStateResponse()
