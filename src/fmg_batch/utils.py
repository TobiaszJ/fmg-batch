"""
FMG-Batch utilities.

This module provides utility functions for the FMG-Batch client.
"""

import json
import os
from glob import glob
from typing import Dict, List, Optional, Tuple, Any

from tqdm import tqdm

from .api.models import Policy, PolicyChange
from .exceptions import FortiManagerFileError


def parse_interfaces(intf_field: Any) -> List[str]:
    """Parse interface fields from different possible formats.

    Args:
        intf_field: Interface field value

    Returns:
        List of interface names
    """
    if isinstance(intf_field, list):
        return [i["name"] if isinstance(i, dict) else str(i) for i in intf_field]
    elif isinstance(intf_field, str):
        return [intf_field]
    elif intf_field is None:
        return []
    else:
        return [str(intf_field)]


def load_policies_from_directory(directory: str) -> Dict[int, Dict]:
    """Load policy files from a directory.

    Args:
        directory: Directory containing policy files

    Returns:
        Dictionary mapping policy IDs to policy data

    Raises:
        FortiManagerFileError: If the directory does not exist
    """
    if not os.path.exists(directory):
        raise FortiManagerFileError(f"Directory not found: {directory}")

    policies = {}
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(directory, filename), "r", encoding="utf-8") as f:
                    policy = json.load(f)
                    if "policyid" in policy:
                        policies[policy["policyid"]] = policy
            except (json.JSONDecodeError, IOError) as e:
                raise FortiManagerFileError(f"Error loading policy file {filename}: {str(e)}")

    return policies


def find_policy_changes(
    original_policies: Dict[int, Dict], modified_policies: Dict[int, Dict], fields: List[str] = None
) -> List[PolicyChange]:
    """Find changes between original and modified policies.

    Args:
        original_policies: Dictionary mapping policy IDs to original policy data
        modified_policies: Dictionary mapping policy IDs to modified policy data
        fields: List of fields to compare (if None, compare all fields)

    Returns:
        List of PolicyChange objects
    """
    if fields is None:
        fields = ["srcintf", "dstintf"]

    changes = []
    for policy_id, modified_policy in modified_policies.items():
        original_policy = original_policies.get(policy_id)
        if original_policy:
            change = PolicyChange(
                policy_id=policy_id, name=modified_policy.get("name", "No Name")
            )
            for key in fields:
                original_value = original_policy.get(key, [])
                modified_value = modified_policy.get(key, [])
                
                # Ensure values are lists of strings for comparison
                if not isinstance(original_value, list):
                    original_value = [str(original_value)] if original_value else []
                if not isinstance(modified_value, list):
                    modified_value = [str(modified_value)] if modified_value else []
                
                # Compare values
                if original_value != modified_value:
                    change.changes[key] = (original_value, modified_value)
            
            if change.changes:
                changes.append(change)

    return changes


def save_policy_to_file(policy: Dict, filename: str) -> None:
    """Save a policy to a file.

    Args:
        policy: Policy data
        filename: Filename to save to

    Raises:
        FortiManagerFileError: If the file cannot be written
    """
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(policy, f, indent=4)
    except IOError as e:
        raise FortiManagerFileError(f"Error writing policy file {filename}: {str(e)}")


def print_policy_changes(changes: List[PolicyChange]) -> None:
    """Print policy changes.

    Args:
        changes: List of PolicyChange objects
    """
    if not changes:
        print("No changes found.")
        return

    print("\nFound changes:\n")
    for change in changes:
        print(f"Policy ID {change.policy_id}: {change.name}")
        for key, (original_value, modified_value) in change.changes.items():
            print(f"  {key}: {', '.join(original_value)} -> {', '.join(modified_value)}")
        print()


def batch_replace_interfaces(
    input_dir: str,
    output_dir: str,
    interface_to_replace: str = "MPLS",
    replacement_interfaces: List[str] = None,
) -> List[PolicyChange]:
    """Replace an interface with multiple interfaces in all policies.
    
    This function finds all policies that have the specified interface in either
    source or destination interfaces and replaces it with the specified list of
    replacement interfaces. Other interfaces in the list are preserved.
    
    Args:
        input_dir: Directory containing policy files
        output_dir: Directory to save modified policy files
        interface_to_replace: Interface to replace
        replacement_interfaces: List of interfaces to replace with
        
    Returns:
        List of PolicyChange objects representing the changes made
        
    Raises:
        FortiManagerFileError: If the input directory does not exist
    """
    if replacement_interfaces is None:
        replacement_interfaces = ["DP_VPN1", "DP_VPN2", "HI_VPN1", "HI_VPN2", "DP-HI-VPN_1", "DP-HI-VPN_2"]
    
    # Load policies
    policies = load_policies_from_directory(input_dir)
    changes = []
    
    # Process each policy
    for policy_id, policy_data in tqdm(policies.items(), desc="Processing policies"):
        modified = False
        modified_policy = policy_data.copy()
        
        # Check source interfaces
        if "srcintf" in policy_data:
            srcintf = policy_data["srcintf"]
            if isinstance(srcintf, list) and interface_to_replace in srcintf:
                # Replace the interface while preserving others
                new_srcintf = [intf for intf in srcintf if intf != interface_to_replace]
                new_srcintf.extend(replacement_interfaces)
                modified_policy["srcintf"] = new_srcintf
                modified = True
        
        # Check destination interfaces
        if "dstintf" in policy_data:
            dstintf = policy_data["dstintf"]
            if isinstance(dstintf, list) and interface_to_replace in dstintf:
                # Replace the interface while preserving others
                new_dstintf = [intf for intf in dstintf if intf != interface_to_replace]
                new_dstintf.extend(replacement_interfaces)
                modified_policy["dstintf"] = new_dstintf
                modified = True
        
        # Save modified policy
        if modified:
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.join(output_dir, f"policy_{policy_id}.json")
            save_policy_to_file(modified_policy, filename)
            
            # Create change object for reporting
            change = PolicyChange(
                policy_id=policy_id,
                name=policy_data.get("name", "No Name")
            )
            if "srcintf" in policy_data and "srcintf" in modified_policy:
                if policy_data["srcintf"] != modified_policy["srcintf"]:
                    change.changes["srcintf"] = (policy_data["srcintf"], modified_policy["srcintf"])
            if "dstintf" in policy_data and "dstintf" in modified_policy:
                if policy_data["dstintf"] != modified_policy["dstintf"]:
                    change.changes["dstintf"] = (policy_data["dstintf"], modified_policy["dstintf"])
            
            changes.append(change)
    
    return changes
