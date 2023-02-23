from qm.grpc.frontend import (
    SimulationRequest,
    ExecutionRequestSimulateSimulationInterfaceQuantumSimulatorInterface,
)
from qm.simulate.interface import SimulatorInterface
from qm.grpc.quantum_simulator.v1 import PhysicalConfig


class QuantumSimulatorInterface(SimulatorInterface):
    def __init__(self, physical_config: PhysicalConfig) -> None:
        super().__init__()
        self._physical_config = physical_config

    def update_simulate_request(self, request: SimulationRequest) -> SimulationRequest:
        request = super().update_simulate_request(request)
        request.simulate.simulation_interface.quantum_simulator = (
            ExecutionRequestSimulateSimulationInterfaceQuantumSimulatorInterface(
                physical_config=bytes(self._physical_config)
            )
        )
        return request
