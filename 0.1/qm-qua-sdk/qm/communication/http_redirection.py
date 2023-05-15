import re
import logging
from typing import Dict, Tuple

import httpx
from betterproto.lib.google.protobuf import Empty

from qm.utils.general_utils import is_debug

logger = logging.getLogger(__name__)


async def send_redirection_check(host: str, port: int, headers: Dict[str, str]) -> Tuple[str, int]:
    async with httpx.AsyncClient(http2=True, follow_redirects=False, http1=False) as client:
        try:
            extended_headers = {"content-type": "application/grpc", "te": "trailers", **headers}
            response = await client.post(f"http://{host}:{port}", headers=extended_headers, content=bytes(Empty()))
            if response.status_code == 302:
                match = re.match("(?P<host>[^:]*):(?P<port>[0-9]*)(/(?P<url>.*))?", response.headers["location"])
                if match:
                    new_host, new_port, _, __ = match.groups()
                    return new_host, int(new_port)
        except httpx.HTTPError:
            if is_debug():
                logger.exception("Failed to check http redirection")
        return host, port
