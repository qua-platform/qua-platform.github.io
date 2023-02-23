from qm.api.base_api import BaseApi, connection_error_handle
from qm.api.models.info import ImplementationInfo, QuaMachineInfo
from qm.api.models.server_details import ConnectionDetails
from qm.io.qualang.api.v1 import InfoServiceStub, GetInfoRequest, GetInfoResponse


@connection_error_handle()
class InfoServiceApi(BaseApi):
    def __init__(self, connection_details: ConnectionDetails):
        super().__init__(connection_details)
        self._stub = InfoServiceStub(self._channel)

    def get_info(self) -> QuaMachineInfo:
        request = GetInfoRequest()
        response: GetInfoResponse = self._execute_on_stub(self._stub.get_info, request)

        return QuaMachineInfo(
            capabilities=response.capabilities,
            implementation=ImplementationInfo(
                name=response.implementation.name,
                version=response.implementation.version,
                url=response.implementation.url,
            ),
        )
