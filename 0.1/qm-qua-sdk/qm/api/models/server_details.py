import dataclasses
from typing import Optional, Dict

from qm.api.models.capabilities import ServerCapabilities
from qm.api.models.info import QuaMachineInfo
from qm.api.models.debug_data import DebugData

MAX_MESSAGE_SIZE = 1024 * 1024 * 100  # 100 mb in bytes
BASE_TIMEOUT = 60


@dataclasses.dataclass
class ConnectionDetails:
    host: str
    port: int
    user_token: str
    credentials: Optional[str]
    max_message_size: int = dataclasses.field(default=MAX_MESSAGE_SIZE)
    headers: Dict[str, str] = dataclasses.field(default_factory=dict)
    timeout: float = dataclasses.field(default=BASE_TIMEOUT)
    debug_data: Optional[DebugData] = dataclasses.field(default=None)


@dataclasses.dataclass
class ServerDetails:
    port: int
    host: str
    qop_version: Optional[str]
    connection_details: ConnectionDetails

    # does it implement the QUA service
    qua_implementation: Optional[QuaMachineInfo]
    capabilities: ServerCapabilities = dataclasses.field(default=None)

    def __post_init__(self):
        self.capabilities = ServerCapabilities.build(
            qua_implementation=self.qua_implementation
        )
