"""
FMG-Batch API data models.

This module provides data models for the FMG-Batch API.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any


@dataclass
class PolicyChange:
    """Represents a change to a firewall policy."""

    policy_id: int
    name: str
    changes: Dict[str, tuple] = field(default_factory=dict)


@dataclass
class Policy:
    """Represents a FortiManager firewall policy."""

    policy_id: int
    name: str
    srcintf: List[str] = field(default_factory=list)
    dstintf: List[str] = field(default_factory=list)
    srcaddr: List[str] = field(default_factory=list)
    dstaddr: List[str] = field(default_factory=list)
    service: List[str] = field(default_factory=list)
    action: int = 1  # Default: allow
    status: int = 1  # Default: enabled
    schedule: List[str] = field(default_factory=lambda: ["always"])
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Policy":
        """Create a Policy object from a dictionary.

        Args:
            data: Dictionary containing policy data

        Returns:
            Policy object
        """
        policy_id = data.get("policyid", 0)
        name = data.get("name", "")
        srcintf = data.get("srcintf", [])
        dstintf = data.get("dstintf", [])
        srcaddr = data.get("srcaddr", [])
        dstaddr = data.get("dstaddr", [])
        service = data.get("service", [])
        action = data.get("action", 1)
        status = data.get("status", 1)
        schedule = data.get("schedule", ["always"])

        # Handle different formats of interface fields
        if isinstance(srcintf, list):
            srcintf = [i["name"] if isinstance(i, dict) else str(i) for i in srcintf]
        elif isinstance(srcintf, str):
            srcintf = [srcintf]
        elif srcintf is None:
            srcintf = []
        else:
            srcintf = [str(srcintf)]

        if isinstance(dstintf, list):
            dstintf = [i["name"] if isinstance(i, dict) else str(i) for i in dstintf]
        elif isinstance(dstintf, str):
            dstintf = [dstintf]
        elif dstintf is None:
            dstintf = []
        else:
            dstintf = [str(dstintf)]

        return cls(
            policy_id=policy_id,
            name=name,
            srcintf=srcintf,
            dstintf=dstintf,
            srcaddr=srcaddr,
            dstaddr=dstaddr,
            service=service,
            action=action,
            status=status,
            schedule=schedule,
            raw_data=data,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Policy object to a dictionary.

        Returns:
            Dictionary containing policy data
        """
        # Start with the raw data
        result = self.raw_data.copy()
        
        # Update with the current values
        result.update({
            "policyid": self.policy_id,
            "name": self.name,
            "srcintf": self.srcintf,
            "dstintf": self.dstintf,
            "srcaddr": self.srcaddr,
            "dstaddr": self.dstaddr,
            "service": self.service,
            "action": self.action,
            "status": self.status,
            "schedule": self.schedule,
        })
        
        return result
