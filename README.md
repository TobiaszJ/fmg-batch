# FMG-Batch

Python client for batch processing firewall policies via the FortiManager API.

## Purpose

FortiManager does not natively support batch processing of firewall policies, nor does it provide a proper export/import functionality. This project was created to fill that gap by enabling bulk operations on policies, such as mass interface replacements and updates, through a simple CLI and Python API.

The development of this project was assisted by an AI agent running Claude 3.7 Sonnet.

## Features

- Download firewall policies from FortiManager
- Process and display policy information
- Compare original and modified policies
- Update policies in FortiManager with changes
- Batch replace interfaces in multiple policies at once

## Installation

### From Source

```bash
git clone https://github.com/TobiaszJ/fmg-batch.git
cd fmg-batch
pip install -e .
```

### Requirements

- Python 3.6+
- requests
- python-dotenv
- tqdm

## Configuration

Create a `.env` file in the project directory with the following variables:

```
FMGR_IP=your-fortimanager-ip-or-hostname
FMGR_USERNAME=your-username
FMGR_PASSWORD=your-password
FMGR_ADOM=your-adom
FMGR_PACKAGE=your-policy-package
FMGR_VERIFY_SSL=false
```

## Usage

### Command Line Interface

The package provides a command-line interface for common operations:

```bash
# Show help
fmg-batch --help

# Download policies
fmg-batch download --output-dir policies

# Process and display policies
fmg-batch process --input-dir policies

# Compare original and modified policies
fmg-batch compare --original-dir policies --modified-dir modified_policies

# Update policies in FortiManager
fmg-batch update --original-dir policies --modified-dir modified_policies

# Batch replace interfaces in policies
fmg-batch batch-replace --input-dir policies --output-dir modified_policies --interface MPLS --replacements DP_VPN1,DP_VPN2,HI_VPN1,HI_VPN2,VPN1,VPN2
```

### Python API

You can also use the package as a Python library:

```python
from fmg_batch.api.client import FortiManagerClient
from fmg_batch.config import FortiManagerConfig

# Load configuration from .env file
config = FortiManagerConfig.from_env()

# Create client
client = FortiManagerClient(
    host=config.host,
    username=config.username,
    password=config.password,
    adom=config.adom,
    package_name=config.package_name,
)

# Use client as a context manager
with client:
    # Get all policies
    policies = client.get_policies()
    
    # Get a specific policy
    policy = client.get_policy(13)
    
    # Update a policy
    client.update_policy(13, {"srcintf": ["new-interface"]})
```

You can also use the utility functions directly:

```python
from fmg_batch.utils import batch_replace_interfaces, print_policy_changes

# Batch replace interfaces in policies
changes = batch_replace_interfaces(
    input_dir="policies",
    output_dir="modified_policies",
    interface_to_replace="x1",
    replacement_interfaces=["x3", "x4"]
)

# Print the changes
print_policy_changes(changes)
```

## Project Structure

```
fmg-batch/
├── src/
│   └── fmg_batch/
│       ├── __init__.py
│       ├── __main__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   └── models.py
│       ├── cli/
│       │   ├── __init__.py
│       │   └── commands.py
│       ├── config.py
│       ├── exceptions.py
│       ├── logger.py
│       └── utils.py
├── .env
├── README.md
├── requirements.txt
└── setup.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
