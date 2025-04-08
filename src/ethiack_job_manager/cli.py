# -*- coding: utf-8 -*-
"""Command-line interface for Ethiack Job Manager

This module provides a command-line interface for interacting with Ethiack's Public API
to manage security scanning jobs. It wraps the functionality in the manager module
with a user-friendly CLI built using rich-click.

Commands:
    check: Verify if a URL is valid for security scanning
    launch: Launch a new security scan job
    cancel: Cancel a running or queued job
    info: Get detailed information about a specific job
    list: List all jobs
    status: Check the current status of a job
    success: Determine if a job completed successfully
    await: Wait for a job to finish and get results

Authentication:
    The CLI requires API credentials to be set via environment variables
    (ETHIACK_API_KEY and ETHIACK_API_SECRET) or in a .env file in the
    current directory.

Examples:
    # Check if a URL is valid for scanning
    job-manager check https://example.com

    # Launch a security scan and wait for results
    job-manager launch https://example.com --wait

    # Get information about a specific job
    job-manager info JOB_UUID
"""

from typing import Optional

import pydantic
import rich_click as click

from ethiack_job_manager import __version__, api_auth, manager, types, utils


click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = False
click.rich_click.SHOW_METAVARS_COLUMN = False
click.rich_click.APPEND_METAVARS_HELP = True

version_message = (f"{click.style(text='Ethiack Job Manager CLI', bold=True)}"
                   f"\nCommand %(prog)s"
                   "\nPackage %(package)s"
                   "\nVersion %(version)s")


@click.group()
@click.version_option(version=__version__,
                      package_name=__name__.split(".")[0],
                      message=version_message)
def cli() -> None:
    """# **Ethiack Job Manager CLI**

    **Description:** CLI for managing jobs using Ethiack's Public API.

    **Requirements:** To use this package, you need to set up the credentials
    for Ethiack's API.
    For this, define `ETHIACK_API_KEY` and `ETHIACK_API_SECRET` with the API
    key and secret, respectively, as environment variables or in a `.env` file
    in the CLI root directory.
    """
    try:
        _ = api_auth()
    except ValueError as err:
        raise click.ClickException(f"{err} See --help for more information.")


@cli.command(name="check",
             help="Check if a URL is valid and a job can be submitted.")
@click.argument("url")
@click.option("--beacon-id", type=int, default=None,
              help="Optional beacon ID to associate with the check.")
@click.option("--event-slug", type=str, default=None,
              help="Optional event slug to associate with the check.")
@click.option("--echo/--no-echo", default=True, show_default=True,
              help="Echo the response using click.")
@click.option("--fail/--no-fail", default=True, show_default=True,
              help="Exit the program with nonzero code if the check fails.")
def _click_check(url: str,
                 beacon_id: Optional[int],
                 event_slug: Optional[str],
                 echo: bool,
                 fail: bool) -> manager.CheckResponse:
    """Check if a URL is valid and a job can be submitted.

    Wrapper for check. See check for more information.

    Raises:
        click.ClickException: If there is a validation error.
    """
    try:
        return manager.check(url=url,
                             beacon_id=beacon_id,
                             event_slug=event_slug,
                             echo=echo,
                             fail=fail)
    except pydantic.ValidationError as err:
        exc = click.ClickException(str(err))
        exc.exit_code = 1 if fail else 0
        raise exc


@cli.command(name="launch", help="Launch a job.")
@click.argument("url")
@click.option("--beacon-id", type=int, default=None,
              help="Optional beacon ID to associate with the job.")
@click.option("--event-slug", type=str, default=None,
              help="Optional event slug to associate with the job.")
@click.option("--wait/--no-wait", default=False, show_default=True,
              help="Wait for the job to finish. Defaults to False.")
@click.option("--echo/--no-echo", default=True, show_default=True,
              help="Echo the response using click.")
@click.option("--timeout", type=int, default=3600, show_default=True,
              help="Maximum time to wait for the job to finish in seconds. "
                   "Defaults to 3600. Only used if wait is True.")
@click.option("--severity",
              type=click.Choice([s.value for s in utils.Severity]),
              default=utils.Severity.MEDIUM.value, show_default=True,
              help="Minimum severity level that should fail. Only used if "
                   "wait is True.")
@click.option("--fail/--no-fail", default=True, show_default=True,
              help="Exit with nonzero code if the job was unsuccessful. "
                   "Defaults to True. Only used if wait is True.")
def _click_launch_job(url: str,
                      beacon_id: Optional[int],
                      event_slug: Optional[str],
                      echo: bool,
                      wait: bool,
                      timeout: int,
                      severity: str,
                      fail: bool
                      ) -> manager.LaunchJobResponse:
    """Launch a job.

    Wrapper for launch_job. See launch_job for more information.

    Raises:
        click.ClickException: If there is a validation error.
    """
    try:
        return manager.launch_job(url=url,
                                  beacon_id=beacon_id,
                                  event_slug=event_slug,
                                  echo=echo,
                                  wait=wait,
                                  timeout=timeout,
                                  severity=utils.Severity[severity.upper()],
                                  fail=fail)
    except pydantic.ValidationError as err:
        exc = click.ClickException(str(err))
        exc.exit_code = 1 if fail else 0
        raise exc


@cli.command(name="cancel", help="Cancel a queued or running job.")
@click.argument("uuid")
@click.option("--echo/--no-echo", default=True, show_default=True,
              help="Echo the response using click.")
def _click_cancel_job(uuid: str, echo: bool) -> manager.CancelJobResponse:
    """Cancel a queued or running job.

    Wrapper for cancel_job. See cancel_job for more information.
    """
    return manager.cancel_job(uuid=uuid, echo=echo)


@cli.command(name="info", help="Get information about a job.")
@click.argument("uuid")
@click.option("--echo/--no-echo", default=True, show_default=True,
              help="Echo the response using click.")
def _click_get_job_info(uuid: str, echo: bool) -> manager.JobInfoResponse:
    """Get information about a job.

    Wrapper for get_job_info. See get_job_info for more information.
    """
    return manager.get_job_info(uuid=uuid, echo=echo)


@cli.command(name="list", help="List all jobs.")
@click.option("--echo/--no-echo", default=True, show_default=True,
              help="Echo the response using click.")
def _click_get_jobs_list(echo: bool) -> manager.ListJobsResponse:
    """List all jobs.

    Wrapper for get_jobs_list. See get_jobs_list for more information.
    """
    return manager.get_jobs_list(echo=echo)


@cli.command(name="status", help="Show the status of a job.")
@click.argument("uuid")
@click.option("--echo/--no-echo", default=True, show_default=True,
              help="Echo the response using click.")
def _click_get_job_status(uuid: str,
                          echo: bool = True) -> manager.JobStatusResponse:
    """Show the status of a job.

    Wrapper for get_job_status. See get_job_status for more information.
    """
    return manager.get_job_status(uuid=uuid, echo=echo)


@cli.command(name="success", help="Show the success of a job.")
@click.argument("uuid")
@click.option("--severity",
              type=click.Choice([s.value for s in utils.Severity]),
              default=utils.Severity.MEDIUM.value, show_default=True,
              help="Minimum severity level that should fail.")
@click.option("--echo/--no-echo", default=True, show_default=True,
              help="Echo the response using click.")
@click.option("--fail/--no-fail", default=True, show_default=True,
              help="Exit with nonzero code if the job was unsuccessful.")
def _click_get_job_success(uuid: str,
                           severity: str,
                           echo: bool,
                           fail: bool) -> manager.JobSuccessResponse:
    """Retrieve the success of a job.

    Wrapper for get_job_success. See get_job_success for more information.
    """
    return manager.get_job_success(uuid=uuid,
                                   severity=utils.Severity[severity.upper()],
                                   echo=echo,
                                   fail=fail)


@cli.command(name="await", help="Wait for a job to finish.")
@click.argument("uuid")
@click.option("--timeout", type=int, default=3600, show_default=True,
              help="Maximum time to wait for the job to finish.")
@click.option("--severity",
              type=click.Choice([s.value for s in utils.Severity]),
              default=utils.Severity.MEDIUM.value, show_default=True,
              help="Minimum severity level that should fail.")
@click.option("--echo/--no-echo", default=True, show_default=True,
              help="Echo the response using click.")
@click.option("--fail/--no-fail", default=True, show_default=True,
              help="Exit with nonzero code if the job was unsuccessful.")
def _click_wait_for_job(uuid: str,
                        severity: str,
                        timeout: int,
                        echo: bool,
                        fail: bool) -> manager.JobSuccessResponse:
    """Wait for a job to finish.

    Wrapper for wait_for_job. See wait_for_job for more information.
    """
    return manager.wait_for_job(uuid=uuid,
                                severity=utils.Severity[severity.upper()],
                                timeout=timeout,
                                echo=echo,
                                fail=fail)
