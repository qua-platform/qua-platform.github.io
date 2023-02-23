from dependency_injector import containers, providers

from qm.api.models.capabilities import ServerCapabilities
from qm.api.models.info import QuaMachineInfo


class CapabilitiesContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    capabilities = providers.Singleton(
        ServerCapabilities.build, qua_implementation=config.qua_implementation
    )


def create_capabilities_container(
    qua_implementation: QuaMachineInfo,
) -> CapabilitiesContainer:
    container = CapabilitiesContainer()
    container.config.qua_implementation.from_value(qua_implementation)
    container.wire(
        modules=[
            "qm.program._qua_config_schema",
            "qm.program._qua_config_to_pb",
            "qm.api.job_manager_api",
        ]
    )
    return container
