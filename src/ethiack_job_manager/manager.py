import json
import typing
import urllib.parse

import pydantic
import requests
import rich_click as click
import tenacity

from ethiack_job_manager import (api_auth, ETHIACK_API_URL,
                                 ETHIACK_API_VER, CONNECT_TIMEOUT, READ_TIMEOUT,
                                 types, utils)

__all__ = ["check", "launch_job", "cancel_job", "get_job_info", "get_jobs_list",
           "get_job_status", "get_job_success",
           "CancelJobResponse", "CheckResponse", "JobInfoResponse",
           "JobStatusResponse", "JobSuccessQuery", "JobSuccessResponse",
           "LaunchJobResponse", "ListJobsResponse"]

T = typing.TypeVar("T", bound=pydantic.BaseModel)


def handle_http_error(err: requests.HTTPError, echo: bool, fail: bool) -> None:
    """Handle HTTP errors.

    This function will handle HTTP errors and print the error message to the
    user. If the error is raised in a click context, it will exit the program
    with exit code 1. Otherwise, it will re-raise the exception.

    Args:
        err (HTTPError): The HTTP error to be handled.
        echo (bool, optional): Echo the response using click.
        fail (bool, optional): Exit the program with nonzero code if the check
            fails.
    Raises:
        requests.HTTPError: Re-raises the HTTP error if not in click context.
    """
    err_msg = str(err)

    if "application/json" in err.response.headers.get("content-type", ""):
        json_response = err.response.json()
        if "error" in json_response:
            additional_info = f"(Error) {json_response['error']}"
        elif "validation_error" in json_response:
            additional_info = (f"(Validation Error) "
                               f"{json_response['validation_error']}")
        else:
            additional_info = f"(Unknown error) {json_response}"

        err_msg = f"{err_msg}\n - Additional info: {additional_info}"

    ctx = click.get_current_context(silent=True)
    if ctx is not None and ctx.command is not None:
        exit_code = 1 if fail else 0
        if echo:
            exc = click.ClickException(err_msg)
            exc.exit_code = exit_code
            raise exc
        else:
            ctx.exit(exit_code)
    else:
        raise requests.exceptions.HTTPError(err_msg, response=err.response)


def process_response(response: requests.Response,
                     model: typing.Type[T],
                     echo: bool = False,
                     fail: bool = True) -> T:
    """Process a response from the API.

    Args:
        response (requests.Response): Response from the API.
        model (T, optional): Pydantic model to validate the response.
        echo (bool, optional): Echo the response using click. Defaults to False.
        fail (bool, optional): Exit the program with nonzero code if the
            response status code is not 2xx or 3xx. Defaults to True.
    Returns:
        T: Validated response object.
    Raises:
        requests.HTTPError: If the response status code is not 2xx or 3xx.
    """
    try:
        response.raise_for_status()
    except requests.HTTPError as err:
        handle_http_error(err, echo=echo, fail=fail)
    response_obj = model.model_validate(response.json())
    if echo:
        click.echo(response_obj.model_dump_json(indent=2))
    return response_obj


class CheckResponse(pydantic.BaseModel):
    """Response object for job validity"""

    url: str
    """URL of the service"""

    valid: bool
    """Whether the job can be submitted"""


def check(url: str | types.Url,
          echo: bool = False,
          fail: bool = True) -> CheckResponse:
    """Check if a URL is valid and a job can be submitted.

    Args:
        url (str | types.Url): URL of the service.
        echo (bool, optional): Echo the response using click. Defaults to False.
        fail (bool, optional): Exit the program with nonzero code if the check
        fails. Defaults to True.
    Returns:
        CheckResponse: Response object for job validity.
    Raises:
        requests.HTTPError: If the response status code is not 2xx or 3xx.
    """

    service = types.Service.model_validate(dict(url=url))
    req_url = urllib.parse.urljoin(ETHIACK_API_URL,
                                   f"{ETHIACK_API_VER}/jobs/check")
    response = requests.post(req_url,
                             auth=api_auth(),
                             headers={"Content-type": "application/json",
                                      "Accept": "application/json"},
                             data=json.dumps({"url": service.url}),
                             timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
    return process_response(response, model=CheckResponse, echo=echo,
                            fail=fail)


class LaunchJobResponse(pydantic.BaseModel):
    """Response from the launch job endpoint."""

    url: str
    """URL of the service"""

    uuid: str
    """UUID of the job"""


def launch_job(url: str | types.Url,
               echo: bool = False,
               wait: bool = False,
               timeout: int = 3600,
               severity: str = utils.Severity.MEDIUM.value,
               fail: bool = True
               ) -> LaunchJobResponse:
    """Launch a job.

    Args:
        url (pydantic.AnyUrl): URL of the service.
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

    service = types.Service.model_validate(dict(url=url))
    req_url = urllib.parse.urljoin(ETHIACK_API_URL,
                                   f"{ETHIACK_API_VER}/jobs/launch")
    response = requests.post(req_url,
                             auth=api_auth(),
                             headers={"Content-type": "application/json",
                                      "Accept": "application/json"},
                             data=json.dumps({"url": service.url}),
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

    success: bool
    """Whether the job was successfully cancelled."""

    message: str
    """Message from the API."""


def cancel_job(uuid: str, echo: bool = False) -> CancelJobResponse:
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

    job: types.JobFindings
    """Job information."""


def get_job_info(uuid: str, echo: bool = False) -> JobInfoResponse:
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

    jobs: list[types.Job]
    """List of jobs."""


def get_jobs_list(echo: bool = False) -> ListJobsResponse:
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
    status: str


def get_job_status(uuid: str, echo: bool = False) -> JobStatusResponse:
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

    severity: utils.Severity
    """Minimum severity level that should fail."""

    fail: bool = True
    """Exit with nonzero code if the job was unsuccessful."""


class JobSuccessResponse(pydantic.BaseModel):
    """Response from the job success endpoint."""

    success: bool | None = None
    """Whether the job was successful."""

    message: str | None = None
    """Message from the API."""


def get_job_success(uuid: str,
                    severity: str,
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

    @tenacity.retry(retry=tenacity.retry_if_result(
        lambda r: not r.success or r.success is None),
        wait=tenacity.wait_random_exponential(multiplier=1, min=1,
                                              max=15),
        stop=tenacity.stop_after_delay(int(timeout)))
    def _retry() -> JobSuccessResponse:
        return get_job_success(uuid=uuid, severity=severity, echo=False,
                               fail=False)

    _retry()

    return get_job_success(uuid=uuid, severity=severity, echo=echo, fail=fail)
