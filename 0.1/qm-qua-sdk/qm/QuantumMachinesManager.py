import warnings

from qm.quantum_machines_manager import QuantumMachinesManager  # noqa

warnings.warn(
    "'qm.QuantumMachinesManager.QuantumMachinesManager' is moved as of 1.1.2 and will be removed in 1.2.0. "
    "use 'qm.QuantumMachinesManager' instead",
    category=DeprecationWarning,
)
