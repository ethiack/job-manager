import enum

__all__ = ["JobStatus", "Severity"]

import typing

import requests
import rich_click as click

from ethiack_job_manager.manager import T


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
