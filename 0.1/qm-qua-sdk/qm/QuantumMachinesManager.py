import ssl
import json
import logging
import warnings
from typing_extensions import TypedDict
from typing import Any, Dict, List, Optional

from qm.octave import QmOctaveConfig
from qm._controller import Controller
from qm.user_config import UserConfig
from qm.exceptions import QmmException
from qm.utils import deprecation_message
from qm.api.frontend_api import FrontendApi
from qm.program import Program, load_config
from qm.QuantumMachine import QuantumMachine
from qm.api.models.debug_data import DebugData
from qm.jobs.simulated_job import SimulatedJob
from qm.logging_utils import set_logging_level
from qm.api.simulation_api import SimulationApi
from qm.api.server_detector import detect_server
from qm.octave.octave_manager import OctaveManager
from qm.simulate.interface import SimulationConfig
from qm.persistence import BaseStore, SimpleFileStore
from qm.api.models.server_details import ServerDetails
from qm.type_hinting.config_types import DictQuaConfig
from qm.program._qua_config_to_pb import load_config_pb
from qm.api.models.compiler import CompilerOptionArguments
from qm.octave.calibration_db import load_from_calibration_db
from qm.program._qua_config_schema import validate_config_capabilities
from qm.containers.capabilities_container import create_capabilities_container

logger = logging.getLogger(__name__)

Version = TypedDict("Version", {"client": str, "server": Optional[str]})


class QuantumMachinesManager:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        *,
        timeout: Optional[float] = None,
        log_level: int = logging.INFO,
        connection_headers: Optional[Dict[str, str]] = None,
        add_debug_data: bool = False,
        credentials: Optional[ssl.SSLContext] = None,
        store: Optional[BaseStore] = None,
        file_store_root: str = ".",
        octave: Optional[QmOctaveConfig] = None,
    ):
        """
        Args:
            host (string): Host where to find the QM orchestrator. If
                ``None``, local settings are used
            port: Port where to find the QM orchestrator. If None, local
                settings are used
        """
        set_logging_level(log_level)

        self._user_config = UserConfig.create_from_file()

        self._port = port
        self._host = host or self._user_config.manager_host or ""
        if self._host is None:
            message = "Failed to connect to QuantumMachines server. No host given."
            logger.error(message)
            raise QmmException(message)

        self._credentials = credentials
        self._store = store if store else SimpleFileStore(file_store_root)

        self._octave_config = octave
        self._octave_manager = OctaveManager(octave, self)

        self._server_details = self._initialize_connection(
            timeout=timeout,
            add_debug_data=add_debug_data,
            connection_headers=connection_headers,
        )

        self._caps = self._server_details.capabilities
        self._frontend = FrontendApi(self._server_details.connection_details)
        self._simulation_api = SimulationApi(self._server_details.connection_details)

        self._octave_config = octave
        self._octave_manager = OctaveManager(self._octave_config, self, self._caps)

        raise_on_error = self._user_config.strict_healthcheck is not False
        self.perform_healthcheck(raise_on_error)

    def _initialize_connection(
        self,
        timeout: Optional[float],
        add_debug_data: bool,
        connection_headers: Optional[Dict[str, str]],
    ) -> ServerDetails:
        server_details = detect_server(
            user_token=self._user_config.user_token,
            ssl_context=self._credentials,
            host=self._host,
            port_from_user_config=self._user_config.manager_port,
            user_provided_port=self._port,
            add_debug_data=add_debug_data,
            timeout=timeout,
            extra_headers=connection_headers,
        )
        create_capabilities_container(server_details.qua_implementation)
        return server_details

    @property
    def store(self) -> BaseStore:
        return self._store

    @property
    def octave_manager(self) -> OctaveManager:
        warnings.warn("Do not use OctaveManager, it will be removed in the next version", DeprecationWarning)
        return self._octave_manager

    def perform_healthcheck(self, strict: bool = True) -> None:
        """Perform a health check against the QM server.

        Args:
            strict: Will raise an exception if health check failed
        """
        self._frontend.healthcheck(strict)

    def version(self) -> Version:
        """
        Returns:
            The SDK and QOP versions
        """
        server_version = self._server_details.qop_version
        from qm.version import __version__

        return {"client": __version__, "server": server_version}

    def reset_data_processing(self) -> None:
        """Stops current data processing for ALL running jobs"""
        self._frontend.reset_data_processing()

    def close(self) -> None:
        """Closes the Quantum machine manager"""
        warnings.warn(
            deprecation_message("QuantumMachineManager.close()", "1.1.0", "1.2.0", "close will be removed."),
            category=DeprecationWarning,
        )
        pass

    def open_qm(
        self,
        config: DictQuaConfig,
        close_other_machines: bool = True,
        validate_with_protobuf: bool = False,
        use_calibration_data: bool = True,
        **kwargs: Any,
    ) -> QuantumMachine:
        """Opens a new quantum machine. A quantum machine can use multiple OPXes, and a
        single OPX can also be used by multiple quantum machines as long as they do not
        share the same physical resources (input/output ports) as defined in the config.

        Args:
            config: The config that will be used by the quantum machine
            close_other_machines: When set to true (default) any open
                quantum machines will be closed. This simplifies the
                workflow, but does not enable opening more than one
                quantum machine.
            validate_with_protobuf (bool): Validates config with
                protobuf instead of marshmallow. It is usually faster
                when working with large configs. Defaults to False.

        Returns:
            A quantum machine obj that can be used to execute programs
        """
        if kwargs:
            logger.warning(f"unused kwargs: {list(kwargs)}, please remove them.")

        if use_calibration_data and self._octave_config is not None and self._octave_config.calibration_db is not None:
            load_from_calibration_db(config, self._octave_config.calibration_db)

        if validate_with_protobuf:
            loaded_config = load_config_pb(config)
        else:
            loaded_config = load_config(config)
        validate_config_capabilities(loaded_config, self._caps)

        machine_id = self._frontend.open_qm(loaded_config, close_other_machines)

        return QuantumMachine(
            machine_id=machine_id,
            pb_config=loaded_config,
            frontend_api=self._frontend,
            capabilities=self._caps,
            store=self._store,
            octave_config=self._octave_config,
            octave_manager=self._octave_manager,
        )

    def open_qm_from_file(self, filename: str, close_other_machines: bool = True) -> QuantumMachine:
        """Opens a new quantum machine with config taken from a file on the local file system

        Args:
            filename: The path to the file that contains the config
            close_other_machines: Flag whether to close all other
                running machines

        Returns:
            A quantum machine obj that can be used to execute programs
        """
        with open(filename) as json_file:
            json1_str = json_file.read()

            def remove_nulls(d: Dict[Any, Any]) -> Dict[Any, Any]:
                return {k: v for k, v in d.items() if v is not None}

            config = json.loads(json1_str, object_hook=remove_nulls)
        return self.open_qm(config, close_other_machines)

    def simulate(
        self,
        config: DictQuaConfig,
        program: Program,
        simulate: SimulationConfig,
        compiler_options: Optional[CompilerOptionArguments] = None,
    ) -> SimulatedJob:
        """Simulate the outputs of a deterministic QUA program.

        The following example shows a simple execution of the simulator, where the
        associated config object is omitted for brevity.

        Example:
            ```python
            from qm.QuantumMachinesManager import QuantumMachinesManager
            from qm.qua import *
            from qm import SimulationConfig

            qmm = QuantumMachinesManager()

            with program() as prog:
                play('pulse1', 'qe1')

            job = qmm.simulate(config, prog, SimulationConfig(duration=100))
            ```
        Args:
            config: A QM config
            program: A QUA ``program()`` object to execute
            simulate: A ``SimulationConfig`` configuration object
            kwargs: additional parameters to pass to execute

        Returns:
            a ``QmJob`` object (see QM Job API).
        """
        if compiler_options is None:
            compiler_options = CompilerOptionArguments()

        job_id, simulated_response_part = self._simulation_api.simulate(config, program, simulate, compiler_options)
        return SimulatedJob(
            job_id=job_id,
            frontend_api=self._frontend,
            capabilities=self._server_details.capabilities,
            store=self._store,
            simulated_response=simulated_response_part,
        )

    def list_open_quantum_machines(self) -> List[str]:
        """Return a list of open quantum machines. (Returns only the ids, use ``get_qm(...)`` to get the machine object)

        Returns:
            The ids list
        """
        return self._frontend.list_open_quantum_machines()

    def get_qm(self, machine_id: str) -> QuantumMachine:
        """Gets an open quantum machine object with the given machine id

        Args:
            machine_id: The id of the open quantum machine to get

        Returns:
            A quantum machine obj that can be used to execute programs
        """
        qm_data = self._frontend.get_quantum_machine(machine_id)
        return QuantumMachine(
            machine_id=qm_data.machine_id,
            pb_config=qm_data.config,
            frontend_api=self._frontend,
            capabilities=self._caps,
            store=self.store,
            octave_manager=self.octave_manager,
        )

    def close_all_quantum_machines(self) -> None:
        """Closes ALL open quantum machines"""
        self._frontend.close_all_quantum_machines()

    def get_controllers(self) -> List[Controller]:
        """Returns a list of all the controllers that are available"""
        return [Controller.build_from_message(message) for message in self._frontend.get_controllers()]

    def clear_all_job_results(self) -> None:
        """Deletes all data from all previous jobs"""
        self._frontend.clear_all_job_results()

    def _send_debug_command(self, controller_name: str, command: str) -> str:
        return self._frontend.send_debug_command(controller_name, command)

    @property
    def _debug_data(self) -> Optional[DebugData]:
        return self._server_details.connection_details.debug_data
