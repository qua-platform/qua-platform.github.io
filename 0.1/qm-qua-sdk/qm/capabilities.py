import warnings

from qm.api.models.capabilities import ServerCapabilities  # noqa

warnings.warn(
    "'qm.capabilities.ServerCapabilities' is moved as of 1.1.0 and will be removed in 1.2.0. "
    "use 'qm.api.models.capabilities.ServerCapabilities' instead",
    category=DeprecationWarning,
)
