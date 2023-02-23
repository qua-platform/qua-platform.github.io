import datetime
from typing import Optional

import betterproto

from qm.api.frontend_api import FrontendApi
from qm.api.job_manager_api import JobManagerApi
from qm.api.models.capabilities import ServerCapabilities
from qm.exceptions import QmQuaException
from qm.grpc.frontend import JobExecutionStatus
from qm.persistence import BaseStore
from qm.utils import deprecate_to_property


class QmBaseJob:
    def __init__(
        self,
        job_id: str,
        machine_id: str,
        frontend_api: FrontendApi,
        capabilities: ServerCapabilities,
        store: BaseStore,
    ):
        self._id = job_id
        self._machine_id = machine_id
        self._frontend = frontend_api
        self._capabilities = capabilities
        self._store = store

        self._job_manager = JobManagerApi.from_api(frontend_api)

        self._added_user_id: Optional[str] = None
        self._time_added: Optional[datetime.datetime] = None
        self._initialize_from_job_status()

    def _initialize_from_job_status(self):
        status: JobExecutionStatus = self._job_manager.get_job_execution_status(
            self._id, self._machine_id
        )
        name, one_of = betterproto.which_one_of(status, "status")

        if name in ("pending", "running", "completed", "loading"):
            self._added_user_id = one_of.added_by
            self._time_added = one_of.time_added

    @property
    def status(self) -> str:
        """Returns the status of the job, one of the following strings:
        "unknown", "pending", "running", "completed", "canceled", "loading", "error"
        """
        status: JobExecutionStatus = self._job_manager.get_job_execution_status(
            self._id, self._machine_id
        )
        name, _ = betterproto.which_one_of(status, "status")
        return name

    @property
    def id(self) -> str:
        """Returns:
        The id of the job
        """
        class_name = self.__class__.__name__
        return deprecate_to_property(
            self._id,
            "1.1.0",
            "1.2.0",
            f"'{class_name}.id()' is deprecated, use '{class_name}.id' instead",
        )

    @property
    def user_added(self) -> Optional[str]:
        return self._added_user_id

    @property
    def time_added(self) -> Optional[datetime.datetime]:
        return self._time_added

    def insert_input_stream(
        self,
        name: str,
        data,
    ):
        """Insert data to the input stream declared in the QUA program.
        The data is then ready to be read by the program using the advance
        input stream QUA statement.

        Multiple data entries can be inserted before the data is read by the program.

        See [Input streams](/qm-qua-sdk/docs/Guides/features/#input-streams) for more information.

        -- Available from QOP 2.0 --

        Args:
            name: The input stream name the data is to be inserted to.
            data: The data to be inserted. The data's size must match
                the size of the input stream.
        """
        if not self._capabilities.supports_input_stream:
            raise QmQuaException(
                "`insert_input_stream()` is not supported by the QOP version."
            )

        if not isinstance(data, list):
            data = [data]

        self._job_manager.insert_input_stream(self.id, name, data)
