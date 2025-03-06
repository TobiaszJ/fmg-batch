"""
FMG-Batch configuration.

This module provides configuration functionality for the FMG-Batch client.
"""

import os
from dataclasses import dataclass
from typing import Dict, Optional

from dotenv import load_dotenv

from .exceptions import FortiManagerConfigError


@dataclass
class FortiManagerConfig:
    """FortiManager API client configuration."""

    host: str
    username: str
    password: str
    adom: str
    package_name: str
    verify_ssl: bool = False

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "FortiManagerConfig":
        """Load configuration from environment variables.

        Args:
            env_file: Path to .env file

        Returns:
            FortiManagerConfig object

        Raises:
            FortiManagerConfigError: If required environment variables are missing
        """
        # Load environment variables from .env file if specified
        if env_file:
            if not os.path.exists(env_file):
                raise FortiManagerConfigError(f"Environment file not found: {env_file}")
            load_dotenv(env_file)
        else:
            load_dotenv()  # Try to load from default .env file

        # Get required environment variables
        host = os.getenv("FMGR_IP")
        username = os.getenv("FMGR_USERNAME")
        password = os.getenv("FMGR_PASSWORD")
        adom = os.getenv("FMGR_ADOM")
        package_name = os.getenv("FMGR_PACKAGE")

        # Validate required environment variables
        missing_vars = []
        if not host:
            missing_vars.append("FMGR_IP")
        if not username:
            missing_vars.append("FMGR_USERNAME")
        if not password:
            missing_vars.append("FMGR_PASSWORD")
        if not adom:
            missing_vars.append("FMGR_ADOM")
        if not package_name:
            missing_vars.append("FMGR_PACKAGE")

        if missing_vars:
            raise FortiManagerConfigError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        # Get optional environment variables
        verify_ssl_str = os.getenv("FMGR_VERIFY_SSL", "false")
        verify_ssl = verify_ssl_str.lower() in ("true", "1", "yes")

        return cls(
            host=host,
            username=username,
            password=password,
            adom=adom,
            package_name=package_name,
            verify_ssl=verify_ssl,
        )

    def to_dict(self) -> Dict[str, str]:
        """Convert the configuration to a dictionary.

        Returns:
            Dictionary containing configuration values
        """
        return {
            "host": self.host,
            "username": self.username,
            "password": "********",  # Mask password for security
            "adom": self.adom,
            "package_name": self.package_name,
            "verify_ssl": str(self.verify_ssl),
        }
