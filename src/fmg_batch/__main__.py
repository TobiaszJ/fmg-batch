"""
FMG-Batch main entry point.

This module provides the main entry point for the FMG-Batch client.
"""

import sys

from .cli.commands import main

if __name__ == "__main__":
    sys.exit(main())
