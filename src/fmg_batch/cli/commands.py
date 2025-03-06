"""
FMG-Batch CLI commands.

This module provides command-line interface commands for the FMG-Batch client.
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional

from tqdm import tqdm

from ..api.client import FortiManagerClient
from ..api.models import Policy, PolicyChange
from ..config import FortiManagerConfig
from ..exceptions import FortiManagerError
from ..logger import setup_logger
from ..utils import (
    batch_replace_interfaces,
    find_policy_changes,
    load_policies_from_directory,
    print_policy_changes,
    save_policy_to_file,
)


def download_policies_command(args: argparse.Namespace) -> int:
    """Download policies command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    logger = setup_logger(level=logging.DEBUG if args.verbose else logging.INFO)
    logger.info("Downloading policies...")

    try:
        config = FortiManagerConfig.from_env(args.env_file)
        
        # Create output directory if it doesn't exist
        output_dir = args.output_dir or "policies"
        os.makedirs(output_dir, exist_ok=True)
        
        with FortiManagerClient(
            host=config.host,
            username=config.username,
            password=config.password,
            adom=config.adom,
            package_name=config.package_name,
            verify_ssl=config.verify_ssl,
        ) as client:
            # Get all policies
            policies = client.get_policies()
            logger.info(f"Found {len(policies)} policies")
            
            # Download each policy
            for policy in tqdm(policies, desc="Downloading policies"):
                policy_id = policy.get("policyid")
                policy_data = client.get_policy(policy_id)
                
                # Save policy to file
                filename = os.path.join(output_dir, f"policy_{policy_id}.json")
                save_policy_to_file(policy_data, filename)
            
            logger.info(f"Successfully downloaded {len(policies)} policies to {output_dir}")
            return 0
    except FortiManagerError as e:
        logger.error(f"Error: {str(e)}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return 1


def process_policies_command(args: argparse.Namespace) -> int:
    """Process policies command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    logger = setup_logger(level=logging.DEBUG if args.verbose else logging.INFO)
    logger.info("Processing policies...")

    try:
        # Load policies from directory
        input_dir = args.input_dir or "policies"
        policies = load_policies_from_directory(input_dir)
        
        if not policies:
            logger.warning(f"No policies found in {input_dir}")
            return 0
        
        logger.info(f"Found {len(policies)} policies")
        
        # Process each policy
        for policy_id, policy_data in sorted(policies.items()):
            policy = Policy.from_dict(policy_data)
            print(f"Policy ID {policy.policy_id}: {policy.name}")
            print(f"  From: {', '.join(policy.srcintf)}")
            print(f"  To: {', '.join(policy.dstintf)}")
            print()
        
        return 0
    except FortiManagerError as e:
        logger.error(f"Error: {str(e)}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return 1


def compare_policies_command(args: argparse.Namespace) -> int:
    """Compare policies command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    logger = setup_logger(level=logging.DEBUG if args.verbose else logging.INFO)
    logger.info("Comparing policies...")

    try:
        # Load original policies
        original_dir = args.original_dir or "policies"
        original_policies = load_policies_from_directory(original_dir)
        
        if not original_policies:
            logger.warning(f"No original policies found in {original_dir}")
            return 1
        
        # Load modified policies
        modified_dir = args.modified_dir or "modified_policies"
        modified_policies = load_policies_from_directory(modified_dir)
        
        if not modified_policies:
            logger.warning(f"No modified policies found in {modified_dir}")
            return 1
        
        # Find changes
        fields = args.fields.split(",") if args.fields else None
        changes = find_policy_changes(original_policies, modified_policies, fields)
        
        # Print changes
        print_policy_changes(changes)
        
        return 0
    except FortiManagerError as e:
        logger.error(f"Error: {str(e)}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return 1


def batch_replace_command(args: argparse.Namespace) -> int:
    """Batch replace interfaces command.
    
    This command replaces a specific interface with multiple interfaces in all policies.
    By default, it replaces "MPLS" with six VPN interfaces.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code
    """
    logger = setup_logger(level=logging.DEBUG if args.verbose else logging.INFO)
    logger.info("Batch replacing interfaces...")
    
    try:
        # Process policies
        input_dir = args.input_dir or "policies"
        output_dir = args.output_dir or "modified_policies"
        interface = args.interface or "MPLS"
        replacements = args.replacements.split(",") if args.replacements else None
        
        logger.info(f"Replacing interface '{interface}' with {replacements or 'default VPN interfaces'}")
        logger.info(f"Input directory: {input_dir}")
        logger.info(f"Output directory: {output_dir}")
        
        changes = batch_replace_interfaces(
            input_dir=input_dir,
            output_dir=output_dir,
            interface_to_replace=interface,
            replacement_interfaces=replacements
        )
        
        # Print changes
        print_policy_changes(changes)
        
        if changes:
            logger.info(f"Successfully processed {len(changes)} policies")
            logger.info(f"Modified policies saved to {output_dir}")
        else:
            logger.info(f"No policies with interface '{interface}' found")
        
        return 0
    except FortiManagerError as e:
        logger.error(f"Error: {str(e)}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return 1


def update_policies_command(args: argparse.Namespace) -> int:
    """Update policies command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    logger = setup_logger(level=logging.DEBUG if args.verbose else logging.INFO)
    logger.info("Updating policies...")

    try:
        config = FortiManagerConfig.from_env(args.env_file)
        
        # Load original policies
        original_dir = args.original_dir or "policies"
        original_policies = load_policies_from_directory(original_dir)
        
        if not original_policies:
            logger.warning(f"No original policies found in {original_dir}")
            return 1
        
        # Load modified policies
        modified_dir = args.modified_dir or "modified_policies"
        modified_policies = load_policies_from_directory(modified_dir)
        
        if not modified_policies:
            logger.warning(f"No modified policies found in {modified_dir}")
            return 1
        
        # Find changes
        fields = args.fields.split(",") if args.fields else None
        changes = find_policy_changes(original_policies, modified_policies, fields)
        
        if not changes:
            logger.info("No changes found")
            return 0
        
        # Print changes
        print_policy_changes(changes)
        
        # Confirm changes
        if not args.yes:
            confirm = input("Do you want to apply these changes? (yes/no): ").strip().lower()
            if confirm != "yes":
                logger.info("Changes not applied")
                return 0
        
        # Apply changes
        with FortiManagerClient(
            host=config.host,
            username=config.username,
            password=config.password,
            adom=config.adom,
            package_name=config.package_name,
            verify_ssl=config.verify_ssl,
        ) as client:
            for change in tqdm(changes, desc="Updating policies"):
                policy_id = change.policy_id
                
                # Create update data with only changed fields
                update_data = {}
                for key, (_, modified_value) in change.changes.items():
                    update_data[key] = modified_value
                
                logger.debug(f"Updating policy {policy_id} with: {json.dumps(update_data)}")
                
                try:
                    # Try standard update first
                    client.update_policy(policy_id, update_data)
                    logger.info(f"Successfully updated policy {policy_id}")
                except FortiManagerError:
                    logger.warning(f"Standard update failed for policy {policy_id}, trying field-by-field update")
                    
                    # If standard update fails, try field-by-field update
                    for key, (_, modified_value) in change.changes.items():
                        try:
                            client.update_policy_field(policy_id, key, modified_value)
                            logger.info(f"Successfully updated field {key} for policy {policy_id}")
                        except FortiManagerError as e:
                            logger.error(f"Failed to update field {key} for policy {policy_id}: {str(e)}")
            
            logger.info("Policy updates completed")
            return 0
    except FortiManagerError as e:
        logger.error(f"Error: {str(e)}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return 1


def setup_parser() -> argparse.ArgumentParser:
    """Set up command-line argument parser.

    Returns:
        Argument parser
    """
    parser = argparse.ArgumentParser(
        description="FMG-Batch client",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--env-file", "-e", help="Path to .env file", default=None
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Download policies command
    download_parser = subparsers.add_parser(
        "download", help="Download policies from FortiManager"
    )
    download_parser.add_argument(
        "--output-dir", "-o", help="Output directory", default="policies"
    )
    download_parser.set_defaults(func=download_policies_command)

    # Process policies command
    process_parser = subparsers.add_parser(
        "process", help="Process downloaded policies"
    )
    process_parser.add_argument(
        "--input-dir", "-i", help="Input directory", default="policies"
    )
    process_parser.set_defaults(func=process_policies_command)

    # Compare policies command
    compare_parser = subparsers.add_parser(
        "compare", help="Compare original and modified policies"
    )
    compare_parser.add_argument(
        "--original-dir", "-o", help="Original policies directory", default="policies"
    )
    compare_parser.add_argument(
        "--modified-dir", "-m", help="Modified policies directory", default="modified_policies"
    )
    compare_parser.add_argument(
        "--fields", "-f", help="Fields to compare (comma-separated)", default=None
    )
    compare_parser.set_defaults(func=compare_policies_command)

    # Update policies command
    update_parser = subparsers.add_parser(
        "update", help="Update policies in FortiManager"
    )
    update_parser.add_argument(
        "--original-dir", "-o", help="Original policies directory", default="policies"
    )
    update_parser.add_argument(
        "--modified-dir", "-m", help="Modified policies directory", default="modified_policies"
    )
    update_parser.add_argument(
        "--fields", "-f", help="Fields to update (comma-separated)", default=None
    )
    update_parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompt"
    )
    update_parser.set_defaults(func=update_policies_command)
    
    # Batch replace command
    batch_replace_parser = subparsers.add_parser(
        "batch-replace", help="Batch replace interfaces in policies"
    )
    batch_replace_parser.add_argument(
        "--input-dir", "-i", help="Input directory", default="policies"
    )
    batch_replace_parser.add_argument(
        "--output-dir", "-o", help="Output directory", default="modified_policies"
    )
    batch_replace_parser.add_argument(
        "--interface", help="Interface to replace", default="MPLS"
    )
    batch_replace_parser.add_argument(
        "--replacements", "-r", 
        help="Replacement interfaces (comma-separated)", 
        default="DP_VPN1,DP_VPN2,HI_VPN1,HI_VPN2,DP-HI-VPN_1,DP-HI-VPN_2"
    )
    batch_replace_parser.set_defaults(func=batch_replace_command)

    return parser


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    parser = setup_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
