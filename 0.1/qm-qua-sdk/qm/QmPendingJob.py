import warnings

from qm.jobs.pending_job import QmPendingJob  # noqa

warnings.warn(
    "'qm.QmPendingJob.QmPendingJob' is moved as of 1.1.0 and will be removed in 1.2.0. "
    "use 'qm.QmPendingJob' instead",
    category=DeprecationWarning,
)
