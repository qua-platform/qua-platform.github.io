from qm.serialization.qua_serializing_visitor import QuaNodeVisitor  # noqa
import warnings

warnings.warn(
    "'qm.QuaNodeVisitor.QuaNodeVisitor' is moved as of 1.1.0 and will be removed in 1.2.0. "
    "use 'qm.serialization.qua_serializing_visitor.QuaNodeVisitor' instead",
    category=DeprecationWarning,
)
