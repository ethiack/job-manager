<!-- MARKDOWN LINKS & IMAGES -->

[version-shield]: https://img.shields.io/github/v/release/ethiack/job-manager?style=for-the-badge
[version-url]: https://github.com/ethiack/job-manager/releases/latest

[license-shield]: https://img.shields.io/github/license/ethiack/job-manager?style=for-the-badge
[license-url]: https://raw.githubusercontent.com/ethiack/job-manager/main/LICENSE

[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/company/ethiack


<!-- README -->
<a name="readme-top"></a>
<div align="center">

<h1>
  <br>
    <img src="https://raw.githubusercontent.com/ethiack/job-manager/main/assets/logo.webp" alt="logo" width="400">
    <br><br>
    Ethiack Job Manager
    <br><br>
</h1>

<h4>Python package for managing jobs using Ethiack's Public API</h4>

[![GitHub Release][version-shield]][version-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<hr />


</div>

## Introduction

This is Python package and command-line interface (CLI) designed as a wrapper around [Ethiack's Public API](https://api.ethiack.com) ([API docs](https://portal.ethiack.com/docs/api/)). It simplifies the management of jobs by providing convenient access to the primary API endpoints related to job operations.


### Features

- Manage jobs through the Ethiack API with ease.
- Command-line interface for quick interaction.
- Compatible with Python 3.8 and higher.
- Easy installation via PyPI.

## Installation

You can install `ethiack-job-manager` using `pip`:

```bash
pip install ethiack-job-manager
```


## Credentials Setup

Using Ethiack's API - and, therefore, this package - requires authentication using an *API Key* and *API Secret*, which can be retrieved in [Ethiack's Portal settings page](https://portal.ethiack.com/settings/api). These credentials must be available as environment variables `ETHIACK_API_KEY` and `ETHIACK_API_SECRET`, repectively, whenever the package is used.

To set up these credentials, you can either set the environment variables directly:

```bash
export ETHIACK_API_KEY=your_api_key
export ETHIACK_API_SECRET=your_api_secret
```

or create a `.env` file:

```plaintext
ETHIACK_API_KEY=your_api_key
ETHIACK_API_SECRET=your_api_secret
```

## Usage

### Command-line Interface

Run the CLI commands to manage jobs through the Ethiack API.

```
❯ ethiack-job-manager --help

 Usage: ethiack-job-manager [OPTIONS] COMMAND [ARGS]...

 Ethiack Job Manager CLI.
 CLI for managing jobs using Ethiack's Public API.

╭─ Options ─────────────────────────────────────────────────────────────╮
│ --version    Show the version and exit.                               │
│ --help       Show this message and exit.                              │
╰───────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────╮
│ await          Wait for a job to finish.                              │
│ cancel         Cancel a queued or running job.                        │
│ check          Check if a URL is valid and a job can be submitted.    │
│ info           Get information about a job.                           │
│ launch         Launch a job.                                          │
│ list           List all jobs.                                         │
│ status         Show the status of a job.                              │
│ success        Show the success of a job.                             │
╰───────────────────────────────────────────────────────────────────────╯
```

### Python Package

Import the package and use the available functions to manage jobs through the Ethiack API. For more information:

```python
import ethiack_job_manager as manager


help(manager)

```



## License

Distributed under the MIT License. See [LICENSE](https://raw.githubusercontent.com/ethiack/job-manager/main/LICENSE) for more information.
