"""Types for the Ethiack Job Manager."""
import datetime

import pydantic

__all__ = ["Service", "Finding", "Job", "JobFindings"]

from typing import Annotated

from ethiack_job_manager import utils

Url = Annotated[pydantic.AnyUrl,
                pydantic.AfterValidator(lambda x: str(x).rstrip('/'))]


class Service(pydantic.BaseModel):
    """Service model"""

    url: Url
    """URL of the service"""


class Finding(pydantic.BaseModel):
    """Finding model"""

    title: str
    """Title of the finding"""

    severity: utils.Severity
    """Severity of the finding"""


class Job(pydantic.BaseModel):
    """Job model"""

    uuid: str
    """UUID of the job"""

    url: str
    """URL of the target service"""

    status: str
    """Status of the job"""

    created: datetime.datetime
    """Timestamp of the job creation"""

    started: datetime.datetime | None = None
    """Timestamp of the job start"""

    finished: datetime.datetime | None = None
    """Timestamp of the job finish"""


class JobFindings(Job):
    """JobFindings model"""

    findings: list[Finding]
    """Findings of the job"""
