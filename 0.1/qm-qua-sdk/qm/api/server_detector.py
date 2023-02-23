import logging
from typing import Optional, Dict, Union, Set, Tuple

from qm.api.frontend_api import FrontendApi
from qm.api.info_service_api import InfoServiceApi
from qm.api.models.debug_data import DebugData
from qm.api.models.info import QuaMachineInfo
from qm.api.models.server_details import (
    ConnectionDetails,
    ServerDetails,
    MAX_MESSAGE_SIZE,
    BASE_TIMEOUT,
)
from qm.exceptions import (
    QmServerDetectionError,
    QMTimeoutError,
    QMConnectionError,
    QMRedirectionError,
)

logger = logging.getLogger(__name__)

DEFAULT_PORTS = (80, 9510)


def detect_server(
    cluster_name: Optional[str],
    user_token: str,
    credentials: str,
    host: str,
    port_from_user_config: int,
    user_provided_port: Optional[int],
    add_debug_data: bool,
    timeout: Optional[float] = None,
    max_message_size: Optional[int] = None,
    extra_headers: Optional[Dict[str, str]] = None,
) -> ServerDetails:
    ports_to_try = _get_ports(port_from_user_config, user_provided_port)

    headers = _create_headers(extra_headers, cluster_name, user_token)

    for port in ports_to_try:
        logger.debug(f"Probing gateway at: {host}:{port}")
        debug_data = DebugData()

        connection_details = ConnectionDetails(
            host=host,
            port=port,
            user_token=user_token,
            credentials=credentials,
            max_message_size=max_message_size if max_message_size else MAX_MESSAGE_SIZE,
            headers=headers,
            timeout=timeout if timeout else BASE_TIMEOUT,
            debug_data=debug_data if add_debug_data else None,
        )

        info, qop_version = _try_connection(connection_details)

        if qop_version:
            logger.debug(f"Gateway discovered at: {host}:{port}")
            return ServerDetails(
                port=port,
                host=host,
                qop_version=qop_version,
                qua_implementation=info,
                connection_details=connection_details,
            )

    targets = ",".join([f"{host}:{port}" for port in ports_to_try])
    message = (
        f"Failed to detect to QuantumMachines server. Tried connecting to {targets}."
    )
    logger.error(message)
    raise QmServerDetectionError(message)


def _try_connection(
    connection_details: ConnectionDetails,
) -> Tuple[QuaMachineInfo, str]:
    frontend = FrontendApi(connection_details)
    info_service = InfoServiceApi(connection_details)

    qop_version = None
    info = None

    try:
        qop_version = frontend.get_version()
        info = info_service.get_info()

    except QMRedirectionError as e:
        logger.debug(f"Connection redirected to: {e.host}:{e.port}")
        connection_details.host = e.host
        connection_details.port = e.port
        return _try_connection(connection_details)

    except (QMConnectionError, OSError, QMTimeoutError) as e:
        logger.debug(f"Connection error: {e}")
        return info, qop_version

    logger.debug(
        f"Established connection to {connection_details.host}:{connection_details.port}"
    )
    return info, qop_version


def _get_ports(
    port_from_config: Optional[int], user_provided_port: Optional[int]
) -> Set[int]:
    if user_provided_port is not None:
        return {user_provided_port}

    ports = set()
    if port_from_config is not None:
        ports.add(int(port_from_config))

    ports.update({int(port) for port in DEFAULT_PORTS})
    return ports


def _create_headers(
    base_headers: Dict[str, str], cluster_name: Optional[str], user_token: Optional[str]
) -> Dict[str, str]:
    headers = {}
    headers.update(base_headers if base_headers is not None else {})

    headers["x-grpc-service"] = "gateway"
    if user_token:
        headers["authorization"] = f"Bearer {user_token}"
    headers.update(_create_cluster_headers(cluster_name))
    return headers


def _create_cluster_headers(cluster_name: Optional[str]) -> Dict[str, Union[str, bool]]:
    if cluster_name:
        return {"cluster_name": cluster_name}
    return {"cluster_name": "Any", "any_cluster": "true"}
