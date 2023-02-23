import logging

from qm.version import __version__  # noqa

from qm.QuantumMachinesManager import QuantumMachinesManager  # noqa
from qm.QuantumMachine import QuantumMachine  # noqa

from qm.jobs.job_queue import QmQueue  # noqa
from qm.jobs.pending_job import QmPendingJob  # noqa
from qm.jobs.qm_job import QmJob  # noqa

from qm.results import (  # noqa
    StreamingResultFetcher,
    SingleStreamingResultFetcher,
    MultipleStreamingResultFetcher,
)

from qm.program import Program, _ResultAnalysis, _Program  # noqa

from qm.api.models.compiler import CompilerOptionArguments  # noqa
from qm.serialization.generate_qua_script import generate_qua_script  # noqa
from qm.logging_utils import config_loggers
from qm.user_config import UserConfig  # noqa

from qm.simulate import (  # noqa
    SimulationConfig,
    InterOpxAddress,
    InterOpxChannel,
    ControllerConnection,
    InterOpxPairing,
    LoopbackInterface,
)

__all__ = [
    "QuantumMachinesManager",
    "QuantumMachine",
    "QmQueue",
    "QmPendingJob",
    "QmJob",
    "StreamingResultFetcher",
    "SingleStreamingResultFetcher",
    "MultipleStreamingResultFetcher",
    "Program",
    "_ResultAnalysis",
    "CompilerOptionArguments",
    "generate_qua_script",
    "config_loggers",
    "UserConfig",
    "SimulationConfig",
    "InterOpxAddress",
    "InterOpxChannel",
    "ControllerConnection",
    "InterOpxPairing",
    "LoopbackInterface",
]

config = UserConfig.create_from_file()
config_loggers(config)


logger = logging.getLogger(__name__)
logger.info(f"Starting session: {config.SESSION_ID}")
