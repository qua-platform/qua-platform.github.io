import ssl
import logging
from typing import Dict, Optional

from grpclib import GRPCError

from qm.api.frontend_api import FrontendApi
from qm.api.models.debug_data import DebugData
from qm.api.info_service_api import InfoServiceApi
from qm.exceptions import QMTimeoutError, QmServerDetectionError
from qm.api.models.server_details import BASE_TIMEOUT, MAX_MESSAGE_SIZE, ServerDetails, ConnectionDetails

logger = logging.getLogger(__name__)

DEFAULT_PORTS = (80, 9510)


def _fill_headers(headers: Dict[str, str], user_token: Optional[str]) -> Dict[str, str]:
    headers.update({"x-grpc-service": "gateway"})
    if user_token:
        headers["authorization"] = f"Bearer {user_token}"
    return headers


def _create_server_info(
    user_token: Optional[str],
    ssl_context: Optional[ssl.SSLContext],
    host: str,
    port: int,
    add_debug_data: bool,
    headers: Dict[str, str],
    timeout: Optional[float] = None,
    max_message_size: Optional[int] = None,
) -> ServerDetails:
    debug_data = DebugData()

    connection_details = ConnectionDetails(
        host=host,
        port=port,
        user_token=user_token,
        ssl_context=ssl_context,
        max_message_size=max_message_size if max_message_size else MAX_MESSAGE_SIZE,
        headers=_fill_headers(headers, user_token),
        timeout=timeout if timeout else BASE_TIMEOUT,
        debug_data=debug_data if add_debug_data else None,
    )

    frontend = FrontendApi(connection_details)
    info_service = InfoServiceApi(connection_details)

    try:
        qop_version = frontend.get_version()
    except (GRPCError, OSError, QMTimeoutError) as e:
        logger.debug(f"Failed fetching version: {e}")
        qop_version = None

    try:
        info = info_service.get_info()
    except (GRPCError, OSError, QMTimeoutError) as e:
        logger.debug(f"Failed getting gateway info: {e}")
        info = None

    details = ServerDetails(
        port=port,
        host=host,
        qop_version=qop_version,
        qua_implementation=info,
        connection_details=connection_details,
    )

    return details


def detect_server(
    user_token: Optional[str],
    ssl_context: Optional[ssl.SSLContext],
    host: str,
    port_from_user_config: Optional[int],
    user_provided_port: Optional[int],
    add_debug_data: bool,
    timeout: Optional[float] = None,
    max_message_size: Optional[int] = None,
    extra_headers: Optional[Dict[str, str]] = None,
) -> ServerDetails:
    if user_provided_port is None:
        possible_ports_to_try = [port_from_user_config, *DEFAULT_PORTS]
        ports_to_try = []
        for port in possible_ports_to_try:
            if port is not None:
                if int(port) not in ports_to_try:
                    ports_to_try.append(int(port))
    else:
        ports_to_try = [user_provided_port]

    if extra_headers is None:
        extra_headers = {}

    for port in ports_to_try:
        detected = _create_server_info(
            user_token,
            ssl_context,
            host,
            port,
            add_debug_data,
            extra_headers,
            timeout,
            max_message_size,
        )
        if detected.qop_version is not None:
            return detected

    targets = ",".join([f"{host}:{port}" for port in ports_to_try])
    message = f"Failed to detect to QuantumMachines server. Tried connecting to {targets}."
    logger.error(message)
    raise QmServerDetectionError(message)
