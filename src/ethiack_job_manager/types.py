# -*- coding: utf-8 -*-
"""Type definitions and Pydantic models for Ethiack Job Manager

This module defines the Pydantic models that represent the data structures used
in the Ethiack Job Manager. These models are used for validating input data,
serializing requests to the API, and parsing responses from the API.

Classes:
    Service: Represents a target service for security scanning
    Finding: Represents a security finding/vulnerability identified in a scan
    Job: Represents metadata about a security scan job
    JobFindings: Extends Job with detailed findings information

Type Annotations:
    Url: A specialized AnyUrl type that strips trailing slashes

The models use Pydantic for validation, serialization, and deserialization,
ensuring type safety and consistent data handling throughout the application.
"""

import datetime

import pydantic

from ethiack_job_manager import utils


__all__ = ["Service", "Finding", "Job", "JobFindings"]


class Service(pydantic.BaseModel):
    """Service model"""

    url: pydantic.AnyUrl = pydantic.Field(
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

    @pydantic.field_serializer("url")
    def serialize_url(self, value: pydantic.AnyUrl) -> str:
        """Serialize URL to string without trailing slash"""
        return str(value).rstrip('/')


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

    url: pydantic.AnyUrl = pydantic.Field(
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
