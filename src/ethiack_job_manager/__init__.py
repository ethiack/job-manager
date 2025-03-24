# -*- coding: utf-8 -*-
"""Ethiack Job Manager - Client for Ethiack's Public API

This package provides a Python client for interacting with Ethiack's Public API
to manage security scanning jobs. It includes functionality to check URL validity,
launch security scans, monitor job status, retrieve results, and more.

The package requires authentication through API credentials, which can be set via
environment variables (ETHIACK_API_KEY and ETHIACK_API_SECRET) or a .env file.

Modules:
    cli: Command-line interface for the job manager
    manager: Core functions for interacting with the Ethiack API
    types: Type definitions and Pydantic models for job-related data
    utils: Utility functions, enums, and helpers

Basic Usage:
    from ethiack_job_manager import manager

    # Check if a URL is valid for scanning
    response = manager.check("https://example.com")

    # Launch a security scan
    job = manager.launch_job("https://example.com")

    # Wait for a job to complete and get results
    success = manager.wait_for_job(job.uuid)
"""

from __future__ import annotations

import os
from importlib import metadata

import dotenv
import requests.auth


try:
    __version__ = metadata.version("ethiack_job_manager")
except metadata.PackageNotFoundError:
    __version__ = "unknown"

dotenv.load_dotenv()

ETHIACK_API_URL = os.getenv("ETHIACK_API_URL", "https://api.ethiack.com")
ETHIACK_API_VER = os.getenv("ETHIACK_API_VER", "v1")


def api_auth() -> requests.auth.HTTPBasicAuth:
    """Get API authentication.

    Retrieve the API key and secret from the environment variables and return
    the basic authentication object.

    Returns:
        requests.auth.HTTPBasicAuth: API authentication
    """
    api_key = os.getenv("ETHIACK_API_KEY", "")
    api_secret = os.getenv("ETHIACK_API_SECRET", "")
    if not api_key or not api_secret:
        raise ValueError("API key and secret must be set (environment variables"
                         " ETHIACK_API_KEY and ETHIACK_API_SECRET).")
    return requests.auth.HTTPBasicAuth(api_key, api_secret)


CONNECT_TIMEOUT_DEFAULT = 3
CONNECT_TIMEOUT = int(os.getenv("CONNECT_TIMEOUT", CONNECT_TIMEOUT_DEFAULT))
READ_TIMEOUT_DEFAULT = 30
READ_TIMEOUT = int(os.getenv("READ_TIMEOUT", READ_TIMEOUT_DEFAULT))


from ethiack_job_manager.manager import *
from ethiack_job_manager.types import *
from ethiack_job_manager.utils import *
