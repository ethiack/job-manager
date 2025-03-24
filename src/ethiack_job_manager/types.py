"""Types for the Ethiack Job Manager."""

import datetime
from typing import Annotated

import pydantic

from ethiack_job_manager import utils


__all__ = ["Service", "Finding", "Job", "JobFindings"]


Url = Annotated[pydantic.AnyUrl,
                pydantic.AfterValidator(lambda x: str(x).rstrip('/'))]


class Service(pydantic.BaseModel):
    """Service model"""

    url: Url = pydantic.Field(
        description="URL of the service"
    )

    beacon_id: int | None = pydantic.Field(
        default=None,
        description="Beacon ID of the service"
    )

    event_slug: str | None = pydantic.Field(
        default=None,
        description="Event slug of the service"
    )


class Finding(pydantic.BaseModel):
    """Finding model"""

    title: str = pydantic.Field(
        description="Title of the finding"
    )

    severity: utils.Severity = pydantic.Field(
        description="Severity of the finding"
    )

class Job(pydantic.BaseModel):
    """Job model"""

    uuid: str = pydantic.Field(
        description="UUID of the job"
    )

    url: str = pydantic.Field(
        description="URL of the target service"
    )

    status: str = pydantic.Field(
        description="Status of the job"
    )

    created: datetime.datetime = pydantic.Field(
        description="Timestamp of the job creation"
    )

    started: datetime.datetime | None = pydantic.Field(
        default=None,
        description="Timestamp of the job start"
    )

    finished: datetime.datetime | None = pydantic.Field(
        default=None,
        description="Timestamp of the job finish"
    )


class JobFindings(Job):
    """JobFindings model"""

    findings: list[Finding] = pydantic.Field(
        description="Findings of the job"
    )
