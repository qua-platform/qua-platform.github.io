import dataclasses
from collections import deque
from typing import Deque

RECEIVED_HEADERS_MAX_SIZE = 10000


@dataclasses.dataclass
class DebugData:
    received_headers: Deque[dict] = dataclasses.field(
        default_factory=lambda: deque(maxlen=RECEIVED_HEADERS_MAX_SIZE)
    )

    def append(self, received_metadata):
        self.received_headers.append(received_metadata)
