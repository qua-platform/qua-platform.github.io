import datetime
import random
from unittest.mock import AsyncMock

import pytest

from qm.api.job_manager_api import JobManagerApi
from qm.api.models.jobs import PendingJobData
from qm.api.models.server_details import ConnectionDetails
from qm.grpc.frontend import (
    HaltRequest,
    ResumeRequest,
    ResumeResponse,
    PausedStatusResponse,
    PausedStatusRequest,
    IsJobRunningResponse,
    IsJobRunningRequest,
    IsJobAcquiringDataResponseAcquiringStatus,
    IsJobAcquiringDataResponse,
    IsJobAcquiringDataRequest,
    JobExecutionStatus,
    GetJobExecutionStatusRequest,
    GetJobExecutionStatusResponse,
    JobQueryParams,
    QueryValueMatcher,
    RemovePendingJobsResponse,
    GetPendingJobsResponse,
    JobExecutionStatusPending,
)
from qm.grpc.general_messages import Matrix
from qm.grpc.job_manager import (
    SetElementCorrectionRequest,
    GetElementCorrectionRequest,
    InsertInputStreamRequest,
    IntStreamData,
    FixedStreamData,
    BoolStreamData,
)
from qm.grpc.qm_manager import GetRunningJobRequest, GetRunningJobResponse


@pytest.fixture
def api():
    connection_details = ConnectionDetails("", 0, "", "")

    api = JobManagerApi(connection_details)
    api._job_manager_stub = AsyncMock()
    api._frontend_stub = AsyncMock()

    yield api


@pytest.fixture
def random_matrix():
    return random.random(), random.random(), random.random(), random.random()


def test_set_element_correction(api, random_matrix):
    api._job_manager_stub.set_element_correction.return_value.correction = Matrix(*random_matrix)

    result = api.set_element_correction("test_job", "test_element", Matrix(*random_matrix))

    api._job_manager_stub.set_element_correction.assert_called_with(
        SetElementCorrectionRequest(job_id="test_job", qe_name="test_element", correction=Matrix(*random_matrix)),
        timeout=api._timeout,
    )
    assert result == random_matrix


def test_get_element_correction(api, random_matrix):
    api._job_manager_stub.get_element_correction.return_value.correction = Matrix(*random_matrix)

    result = api.get_element_correction("test_job", "test_element")

    api._job_manager_stub.get_element_correction.assert_called_with(
        GetElementCorrectionRequest(job_id="test_job", qe_name="test_element"), timeout=api._timeout
    )
    assert result == random_matrix


@pytest.mark.parametrize(
    "data, data_type, data_object",
    [
        ([1, 2, 3], "int_stream_data", IntStreamData),
        ([1.0, 2.0, 3.0], "fixed_stream_data", FixedStreamData),
        ([True, False, True], "bool_stream_data", BoolStreamData),
    ],
)
def test_insert_input_stream(api, data, data_type, data_object):
    api.insert_input_stream("test_job", "test_stream", data)

    api._job_manager_stub.insert_input_stream.assert_called_with(
        InsertInputStreamRequest(
            job_id="test_job", stream_name="input_stream_test_stream", **{data_type: data_object(data=data)}
        ),
        timeout=api._timeout,
    )


def test_halt(api):
    api.halt("test_job")

    api._frontend_stub.halt.assert_called_with(HaltRequest(job_id="test_job"), timeout=api._timeout)


def test_resume(api):
    api._frontend_stub.resume.return_value = ResumeResponse()

    result = api.resume("test_job")

    api._frontend_stub.resume.assert_called_with(ResumeRequest(job_id="test_job"), timeout=api._timeout)
    assert result


def test_is_paused(api):
    api._frontend_stub.paused_status.return_value = PausedStatusResponse(is_paused=True)

    result = api.is_paused("test_job")

    api._frontend_stub.paused_status.assert_called_with(PausedStatusRequest(job_id="test_job"), timeout=api._timeout)
    assert result


def test_is_job_running(api):
    api._frontend_stub.is_job_running.return_value = IsJobRunningResponse(is_running=True)

    result = api.is_job_running("test_job")

    api._frontend_stub.is_job_running.assert_called_with(IsJobRunningRequest(job_id="test_job"), timeout=api._timeout)
    assert result


def test_is_data_acquiring(api):
    api._frontend_stub.is_job_acquiring_data.return_value = IsJobAcquiringDataResponse(
        acquiring_status=IsJobAcquiringDataResponseAcquiringStatus.ACQUIRE_STOPPED
    )

    result = api.is_data_acquiring("test_job")

    api._frontend_stub.is_job_acquiring_data.assert_called_with(
        IsJobAcquiringDataRequest(job_id="test_job"), timeout=api._timeout
    )
    assert result == IsJobAcquiringDataResponseAcquiringStatus.ACQUIRE_STOPPED


def test_get_job_execution_status(api):
    api._frontend_stub.get_job_execution_status.return_value = GetJobExecutionStatusResponse()

    result = api.get_job_execution_status("test_job", "machine_id")

    api._frontend_stub.get_job_execution_status.assert_called_with(
        GetJobExecutionStatusRequest(job_id="test_job", quantum_machine_id="machine_id"), timeout=api._timeout
    )
    assert result == JobExecutionStatus()


def test_remove_job(api):
    # Set the return value for the 'remove_pending_jobs' method of the mock stub
    api._frontend_stub.remove_pending_jobs.return_value = RemovePendingJobsResponse(numbers_of_jobs_removed=1)

    # Call the remove_job method of the api instance
    result = api.remove_job("test_quantum_machine_id", "test_job", 1, "test_user_id")

    # Assert that the remove_pending_jobs method of the mock stub was called with the correct arguments
    api._frontend_stub.remove_pending_jobs.assert_called_with(
        JobQueryParams(
            quantum_machine_id="test_quantum_machine_id",
            job_id=QueryValueMatcher(value="test_job"),
            position=1,
            user_id=QueryValueMatcher(value="test_user_id"),
        ),
        timeout=api._timeout,
    )
    # Assert that the correct value was returned by the api method
    assert result == 1


def test_get_pending_jobs(api):
    api._frontend_stub.get_pending_jobs.return_value = GetPendingJobsResponse(
        pending_jobs={
            "test_job_1": JobExecutionStatusPending(position_in_queue=1),
            "test_job_2": JobExecutionStatusPending(position_in_queue=2),
            "test_job_3": JobExecutionStatusPending(position_in_queue=3),
        }
    )

    result = api.get_pending_jobs("test_quantum_machine_id", "test_job", 1, "test_user_id")

    api._frontend_stub.get_pending_jobs.assert_called_with(
        JobQueryParams(
            quantum_machine_id="test_quantum_machine_id",
            job_id=QueryValueMatcher(value="test_job"),
            position=1,
            user_id=QueryValueMatcher(value="test_user_id"),
        ),
        timeout=api._timeout,
    )

    assert result == [
        PendingJobData("test_job_1", 1, datetime.datetime(1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc), ""),
        PendingJobData("test_job_2", 2, datetime.datetime(1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc), ""),
        PendingJobData("test_job_3", 3, datetime.datetime(1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc), ""),
    ]


def test_get_running_job(api):
    api._frontend_stub.get_running_job.return_value = GetRunningJobResponse(job_id="test_job")

    result = api.get_running_job("test_machine_id")

    api._frontend_stub.get_running_job.assert_called_with(
        GetRunningJobRequest(machine_id="test_machine_id"), timeout=api._timeout
    )
    assert result == "test_job"
