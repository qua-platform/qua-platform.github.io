import pytest

from qm.api.job_manager_api import JobManagerApi
from qm.api.models.capabilities import ServerCapabilities
from qm.api.models.info import QuaMachineInfo, ImplementationInfo
from qm.api.models.server_details import ServerDetails, ConnectionDetails
from qm.api.stubs.deprecated_job_manager_stub import DeprecatedJobManagerServiceStub
from qm.containers.capabilities_container import create_capabilities_container
from qm.grpc.job_manager import JobManagerServiceStub


@pytest.mark.parametrize(
    "capabilities,supports",
    [
        (QuaMachineInfo([], ImplementationInfo("", "", "")), False),
        (QuaMachineInfo(["qm.random_capability"], ImplementationInfo("", "", "")), False),
        (QuaMachineInfo(["qm.job_streaming_state"], ImplementationInfo("", "", "")), True),
    ],
)
def test_detecting_streaming_job_support_without_qua_impl(capabilities, supports):
    caps = ServerCapabilities.build(capabilities)
    assert caps.has_job_streaming_state == supports


@pytest.mark.parametrize(
    "capabilities, stub_type",
    [
        (["qm.new_grpc_structure"], JobManagerServiceStub),
        ([], DeprecatedJobManagerServiceStub)
    ]
)
def test_new_grpc_structure(capabilities, stub_type):
    create_capabilities_container(QuaMachineInfo(capabilities, ImplementationInfo("", "", "")))
    details = ConnectionDetails(ssl_context="", user_token="", host="", port=1)
    job_manager_api = JobManagerApi(details)
    assert isinstance(job_manager_api._job_manager_stub, stub_type)
