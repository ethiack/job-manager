import enum

__all__ = ["JobStatus", "Severity"]


class JobStatus(str, enum.Enum):
    """Job status enum class."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"
    ERROR = "ERROR"
    CANCELED = "CANCELED"


class Severity(str, enum.Enum):
    """Severity enum class."""
    COSMIC = "cosmic"
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    NONE = "none"
