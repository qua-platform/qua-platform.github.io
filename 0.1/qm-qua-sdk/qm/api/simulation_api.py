import logging
from typing import Tuple, Callable

from qm.simulate import interface
from qm.simulate.interface import SimulationConfig
from qm.program import Program
from qm.api.base_api import BaseApi
from qm.api.models.compiler import (
    CompilerOptionArguments,
    _get_request_compiler_options,
)
from qm.api.models.server_details import ConnectionDetails
from qm.exceptions import QMSimulationError, FailedToExecuteJobException
from qm.grpc.frontend import (
    FrontendStub,
    SimulatedResponsePart,
    SimulationRequest,
    ExecutionRequestSimulate,
    InterOpxAddress,
    InterOpxConnection,
    InterOpxConnectionAddressToAddress,
    InterOpxChannel,
    InterOpxConnectionChannelToChannel,
    SimulationResponse,
    GetSimulatedQuantumStateRequest,
    GetSimulatedQuantumStateResponse,
)
from qm.grpc.qua_config import QuaConfig
from qm.grpc.results_analyser import (
    PullSimulatorSamplesRequest,
    SimulatorSamplesResponse,
)
from qm.program import load_config
from qm.utils import _level_map

logger = logging.getLogger(__name__)


class SimulationApi(BaseApi):
    def __init__(self, connection_details: ConnectionDetails):
        super().__init__(connection_details)
        self._stub = FrontendStub(self._channel)

    def simulate(
        self,
        config: QuaConfig,
        program: Program,
        simulate: SimulationConfig,
        compiler_options: CompilerOptionArguments(),
    ) -> Tuple[str, SimulatedResponsePart]:

        if type(program) is not Program:
            raise Exception("program argument must be of type qm.program.Program")

        request = SimulationRequest()
        msg_config = load_config(config)
        request.config = msg_config

        if type(simulate) is SimulationConfig:
            request.simulate = ExecutionRequestSimulate(
                duration=simulate.duration,
                include_analog_waveforms=simulate.include_analog_waveforms,
                include_digital_waveforms=simulate.include_digital_waveforms,
                extra_processing_timeout_ms=simulate.extraProcessingTimeoutInMs,
            )
            request = simulate.update_simulate_request(request)

            for connection in simulate.controller_connections:
                if not isinstance(connection.source, type(connection.target)):
                    raise Exception(
                        f"Unsupported InterOpx connection. Source is "
                        f"{type(connection.source).__name__} but target is "
                        f"{type(connection.target).__name__}"
                    )

                if isinstance(connection.source, interface.InterOpxAddress):
                    con = InterOpxConnection(
                        address_to_address=InterOpxConnectionAddressToAddress(
                            source=InterOpxAddress(
                                controller=connection.source.controller,
                                left=connection.source.is_left_connection,
                            ),
                            target=InterOpxAddress(
                                controller=connection.target.controller,
                                left=connection.target.is_left_connection,
                            ),
                        )
                    )
                elif isinstance(connection.source, interface.InterOpxChannel):
                    con = InterOpxConnection(
                        channel_to_channel=InterOpxConnectionChannelToChannel(
                            source=InterOpxChannel(
                                controller=connection.source.controller,
                                channel_number=connection.source.channel_number,
                            ),
                            target=InterOpxChannel(
                                controller=connection.target.controller,
                                channel_number=connection.target.channel_number,
                            ),
                        )
                    )
                else:
                    raise Exception(
                        f"Unsupported InterOpx connection. Source is "
                        f"{type(connection.source).__name__}. Supported types are "
                        f"InterOpxAddress "
                        f"or InterOpxChannel"
                    )

                request.controller_connections.append(con)

        request.high_level_program = program.build(msg_config)
        request.high_level_program.compiler_options = _get_request_compiler_options(
            compiler_options
        )

        logger.info("Simulating program")

        response: SimulationResponse = self._execute_on_stub(
            self._stub.simulate, request
        )

        messages = [(_level_map[msg.level], msg.message) for msg in response.messages]

        config_messages = [
            (_level_map[msg.level], msg.message)
            for msg in response.config_validation_errors
        ]

        job_id = response.job_id

        for lvl, msg in messages:
            logger.log(lvl, msg)

        for lvl, msg in config_messages:
            logger.log(lvl, msg)

        if not response.success:
            logger.error("Job " + job_id + " failed. Failed to execute program.")
            for error in response.simulated.errors:
                logger.error(f"Simulation error: {error}")
            raise FailedToExecuteJobException(job_id)

        return job_id, response.simulated

    def get_simulated_quantum_state(self, job_id: str):
        request = GetSimulatedQuantumStateRequest(job_id=job_id)
        response: GetSimulatedQuantumStateResponse = self._execute_on_stub(
            self._stub.get_simulated_quantum_state, request
        )

        if response.ok:
            return response.state

        raise QMSimulationError("Error while pulling quantum state")

    def pull_simulator_samples(
        self,
        job_id: str,
        include_analog: bool,
        include_digital: bool,
        callback: Callable[[SimulatorSamplesResponse], bool],
    ):
        request = PullSimulatorSamplesRequest(
            job_id=job_id,
            include_analog=include_analog,
            include_digital=include_digital,
            include_all_connections=True,
        )

        self._execute_iterator_on_stub(
            self._stub.pull_simulator_samples, callback, request
        )
