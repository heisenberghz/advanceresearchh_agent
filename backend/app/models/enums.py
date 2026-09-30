"""Enumerations for ResearchOps domain models."""

from enum import Enum


class TrustTag(str, Enum):
    """Deterministic trust level assigned to verified facts."""

    GREEN = "GREEN"    # Strongly supported by sufficient credible/recent evidence
    YELLOW = "YELLOW"  # Evidence exists but has limitations (older, single source, minor dispute)
    RED = "RED"        # Weak, unsupported, unverified, or severe unresolved conflict


class VerificationStatus(str, Enum):
    """Status assigned by the independent Checker."""

    VERIFIED = "verified"
    UNCERTAIN = "uncertain"
    CONFLICTING = "conflicting"
    UNSUPPORTED = "unsupported"
    MISSING = "missing"


class JobStatus(str, Enum):
    """Execution status of a discrete research job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    NEEDS_RETRY = "needs_retry"
    FAILED = "failed"


class RunStatus(str, Enum):
    """Overall status of a full research run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ConflictStatus(str, Enum):
    """Resolution status for conflicting claims."""

    UNRESOLVED = "unresolved"
    EXPLAINED = "explained"
    RESOLVED = "resolved"
