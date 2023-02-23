import datetime
from dataclasses import dataclass
from enum import Enum


class InsertDirection(Enum):
    start = 1
    end = 2


@dataclass(frozen=True)
class PendingJobData:
    job_id: str
    position_in_queue: int
    time_added: datetime.datetime
    added_by: str
