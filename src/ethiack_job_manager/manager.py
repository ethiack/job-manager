# -*- coding: utf-8 -*-
"""Core API client functions for Ethiack Job Manager

This module provides the core functions for interacting with Ethiack's Public API
to manage security scanning jobs. It includes functions to check URL validity,
launch jobs, cancel jobs, get job information, monitor status, and determine
job success.

Each function corresponds to a specific API endpoint and returns a Pydantic model
representing the API response. The module handles authentication, request formatting,
error handling, and response parsing.

Functions:
    check: Verify if a URL is valid for security scanning
    launch_job: Launch a new security scan job
    cancel_job: Cancel a running or queued job
    get_job_info: Get detailed information about a specific job
    get_jobs_list: List all jobs
    get_job_status: Check the current status of a job
    get_job_success: Determine if a job completed successfully
    wait_for_job: Wait for a job to finish with exponential backoff

The module uses the requests library for HTTP communication and tenacity
for implementing retry logic when waiting for jobs to complete.
"""

import typing
import urllib.parse

import pydantic
import requests
import tenacity

from ethiack_job_manager import (api_auth, CONNECT_TIMEOUT, ETHIACK_API_URL,
                                 ETHIACK_API_VER, READ_TIMEOUT, types, utils)
from ethiack_job_manager.utils import process_response


__all__ = ["check", "launch_job", "cancel_job", "get_job_info", "get_jobs_list",
           "get_job_status", "get_job_success",
           "CancelJobResponse", "CheckResponse", "JobInfoResponse",
           "JobStatusResponse", "JobSuccessQuery", "JobSuccessResponse",
           "LaunchJobResponse", "ListJobsResponse"]



T = typing.TypeVar("T", bound=pydantic.BaseModel)


class CheckResponse(pydantic.BaseModel):
    """Response object for job validity"""

    url: str = pydantic.Field(description="URL of the service")
    valid: bool = pydantic.Field(description="Whether the job is valid")


def check(url: str | pydantic.AnyUrl,
          *,
          beacon_id: int | None = None,
          event_slug: str | None = None,
          echo: bool = False,
          fail: bool = True) -> CheckResponse:
    """Check if a URL is valid and a job can be submitted.

    Args:
        url (str | pydantic.AnyUrl): URL of the service.
        beacon_id (int | None): Beacon ID of the service. Defaults to None.
        event_slug (str | None): Event slug of the service. Defaults to None.
        echo (bool, optional): Echo the response using click. Defaults to False.
        fail (bool, optional): Exit the program with nonzero code if the check
        fails. Defaults to True.
    Returns:
        CheckResponse: Response object for job validity.
    Raises:
        requests.HTTPError: If the response status code is not 2xx or 3xx.
    """

    service = types.Service.model_validate(dict(url=url, beacon_id=beacon_id,
                                                event_slug=event_slug))
    req_url = urllib.parse.urljoin(ETHIACK_API_URL,
                                   f"{ETHIACK_API_VER}/jobs/check")
    response = requests.post(req_url,
                             auth=api_auth(),
                             headers={"Content-type": "application/json",
                                      "Accept": "application/json"},
                             data=service.model_dump_json(),
                             timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
    return process_response(response, model=CheckResponse, echo=echo,
                            fail=fail)


class LaunchJobResponse(pydantic.BaseModel):
    """Response from the launch job endpoint."""

    url: str = pydantic.Field(description="URL of the service")
    uuid: str = pydantic.Field(description="UUID of the job")
    success: bool = pydantic.Field(
        default=True,
        description="Whether the job was successfully launched."
    )


def launch_job(url: str | pydantic.AnyUrl,
               *,
               beacon_id: int | None = None,
               event_slug: str | None = None,
               echo: bool = False,
               wait: bool = False,
               timeout: int = 3600,
               severity: str = utils.Severity.MEDIUM.value,
               fail: bool = True
               ) -> LaunchJobResponse:
    """Launch a job.
    
    Args:
        url (pydantic.AnyUrl): URL of the service.
        beacon_id (int | None): Beacon ID of the service. Defaults to None.
        event_slug (str | None): Event slug of the service. Defaults to None.
        echo (bool, optional): Echo the response using click. Defaults to False.
        wait (bool, optional): Wait for the job to finish. Defaults to False.
        timeout (int, optional): Maximum time to wait for the job to finish in
            seconds. Defaults to 3600. Only used if wait is True.
        severity (str): Minimum severity level that should fail. Only used if
            wait is True.
        fail (bool, optional): Exit with nonzero code if the job was
            unsuccessful. Defaults to True. Only used if wait is True.
    Returns:
        LaunchJobResponse: Response from the launch job endpoint.
    Raises:
        requests.HTTPError: If the response status code is not 2xx or 3xx.
    """

    service = types.Service.model_validate(dict(url=url, beacon_id=beacon_id,
                                                event_slug=event_slug))
    req_url = urllib.parse.urljoin(ETHIACK_API_URL,
                                   f"{ETHIACK_API_VER}/jobs/launch")
    response = requests.post(req_url,
                             auth=api_auth(),
                             headers={"Content-type": "application/json",
                                      "Accept": "application/json"},
                             data=service.model_dump_json(),
                             timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))

    launch_info = process_response(response, model=LaunchJobResponse, echo=echo)
    if wait:
        _ = wait_for_job(uuid=launch_info.uuid,
                         severity=severity,
                         timeout=timeout,
                         echo=echo,
                         fail=fail)
    return launch_info


class CancelJobResponse(pydantic.BaseModel):
    """Response from the cancel job endpoint."""

    success: bool = pydantic.Field(
        description="Whether the job was successfully cancelled."
    )

    message: str = pydantic.Field(
        alias="description",
        description="Message from the API"
    )

    class Config:
        populate_by_name = True


def cancel_job(uuid: str, *, echo: bool = False) -> CancelJobResponse:
    """Cancel a queued or running job.

    Args:
        uuid (str): UUID of the job.
        echo (bool, optional): Echo the response using click. Defaults to False.
    Returns:
        CancelJobResponse: Response from the cancel job endpoint.
    Raises:
        requests.HTTPError: If the response status code is not 2xx or 3xx.
    """
    req_url = urllib.parse.urljoin(ETHIACK_API_URL,
                                   f"{ETHIACK_API_VER}/jobs/{uuid}/cancel")
    response = requests.post(req_url,
                             auth=api_auth(),
                             timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
    return process_response(response, model=CancelJobResponse, echo=echo)


class JobInfoResponse(pydantic.BaseModel):
    """Response from the job info endpoint."""

    job: types.JobFindings = pydantic.Field(description="Job information")


def get_job_info(uuid: str, *, echo: bool = False) -> JobInfoResponse:
    """Get information about a job.

    Args:
        uuid (str): UUID of the job.
        echo (bool, optional): Echo the response using click. Defaults to False.
    Returns:
        JobInfoResponse: Response from the job info endpoint.
    Raises:
        requests.HTTPError: If the response status code is not 2xx or 3xx.
    """
    req_url = urllib.parse.urljoin(ETHIACK_API_URL,
                                   f"{ETHIACK_API_VER}/jobs/{uuid}")
    response = requests.get(req_url,
                            auth=api_auth(),
                            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
    return process_response(response, model=JobInfoResponse, echo=echo)


class ListJobsResponse(pydantic.BaseModel):
    """Response from the list jobs endpoint."""

    jobs: list[types.Job] = pydantic.Field(description="List of jobs")


def get_jobs_list(*, echo: bool = False) -> ListJobsResponse:
    """List all jobs.

    Args:
        echo (bool, optional): Echo the response using click. Defaults to False.
    Returns:
        ListJobsResponse: Response from the list jobs endpoint.
    Raises:
        requests.HTTPError: If the response status code is not 2xx or 3xx.
    """
    req_url = urllib.parse.urljoin(ETHIACK_API_URL,
                                   f"{ETHIACK_API_VER}/jobs")
    response = requests.get(req_url,
                            auth=api_auth(),
                            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
    return process_response(response, model=ListJobsResponse, echo=echo)


class JobStatusResponse(pydantic.BaseModel):
    status: str = pydantic.Field(description="Status of the job")


def get_job_status(uuid: str, *, echo: bool = False) -> JobStatusResponse:
    """Show the status of a job.

    Args:
        uuid (str): UUID of the job.
        echo (bool, optional): Echo the response using click. Defaults to False.
    Returns:
        JobStatusResponse: Response from the job status endpoint.
    Raises:
        requests.HTTPError: If the response status code is not 2xx or 3xx.
    """
    req_url = urllib.parse.urljoin(ETHIACK_API_URL,
                                   f"{ETHIACK_API_VER}/jobs/{uuid}/status")
    response = requests.get(req_url,
                            auth=api_auth(),
                            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))

    return process_response(response, model=JobStatusResponse, echo=echo)


class JobSuccessQuery(pydantic.BaseModel):
    """Query parameters for the job success endpoint."""

    severity: utils.Severity = pydantic.Field(
        description="Minimum severity level that should fail."
    )

    fail: bool = pydantic.Field(
        default=True,
        description="Exit with nonzero code if the job was unsuccessful."
    )


class JobSuccessResponse(pydantic.BaseModel):
    """Response from the job success endpoint."""

    success: bool | None = pydantic.Field(
        default=None,
        description="Whether the job was successful."
    )

    message: str | None = pydantic.Field(
        default=None,
        alias="description",
        description="Message from the API."
    )

    class Config:
        populate_by_name = True


def get_job_success(uuid: str,
                    severity: str,
                    *,
                    echo: bool = False,
                    fail: bool = True) -> JobSuccessResponse:
    """Retrieve the success of a job.

    Args:
        uuid (str): UUID of the job.
        severity (str): Minimum severity level that should fail.
        echo (bool, optional): Echo the response using click. Defaults to False.
        fail (bool, optional): Exit with nonzero code if the job was
        unsuccessful. Defaults to True.
    Returns:
        JobSuccessResponse: Response from the job success endpoint.
    Raises:
        requests.HTTPError: If the response status code is not 2xx or 3xx.
    """
    path = f"{ETHIACK_API_VER}/jobs/{uuid}/success"
    query = JobSuccessQuery.model_validate(dict(severity=severity,
                                                fail=fail))

    req_url = urllib.parse.urljoin(ETHIACK_API_URL, path)
    response = requests.get(req_url,
                            auth=api_auth(),
                            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                            params=query
                            )
    return process_response(response, model=JobSuccessResponse, echo=echo,
                            fail=fail)


def wait_for_job(uuid: str,
                 *,
                 severity: str = utils.Severity.MEDIUM.value,
                 timeout: int = 3600,
                 echo: bool = False,
                 fail: bool = True) -> JobSuccessResponse:
    """Wait for a job to finish.

    This function will wait for a job to finish. It will retry until the job is
    finished or the timeout is reached.

    Args:
        uuid (str): UUID of the job.
        timeout (int, optional): Maximum time to wait for the job to finish.
            Defaults to 3600.
        severity (str): Minimum severity level that should fail.
        echo (bool, optional): Echo the response using click. Defaults to False.
        fail (bool, optional): Exit with nonzero code if the job was
        unsuccessful. Defaults to True.
    Returns:
        JobSuccessResponse: Response from the job success endpoint.
    Raises:
        requests.HTTPError: If the response status code is not 2xx or 3xx.
    """

    @tenacity.retry(retry=tenacity.retry_if_result(lambda r: r.success is None),
                    wait=tenacity.wait_random_exponential(multiplier=1, min=1, max=15),
                    stop=tenacity.stop_after_delay(int(timeout)))
    def _retry() -> JobSuccessResponse:
        return get_job_success(uuid=uuid, severity=severity, echo=False,
                               fail=False)

    _retry()

    return get_job_success(uuid=uuid, severity=severity, echo=echo, fail=fail)
