"""
FMG-Batch API Client.

This module provides a client for interacting with the FortiManager API.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Union, Any

import requests
import urllib3

from ..exceptions import FortiManagerAPIError, FortiManagerAuthError

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class FortiManagerClient:
    """FortiManager API client for interacting with the FortiManager API."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        adom: str,
        package_name: str,
        verify_ssl: bool = False,
    ):
        """Initialize the FortiManager API client.

        Args:
            host: FortiManager hostname or IP address
            username: FortiManager username
            password: FortiManager password
            adom: FortiManager ADOM name
            package_name: FortiManager policy package name
            verify_ssl: Whether to verify SSL certificates
        """
        self.host = host
        self.username = username
        self.password = password
        self.adom = adom
        self.package_name = package_name
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session_id = None
        self.base_url = f"https://{self.host}/jsonrpc"
        self.request_id = 1

    def login(self) -> None:
        """Login to FortiManager API.

        Raises:
            FortiManagerAuthError: If login fails
        """
        login_payload = {
            "method": "exec",
            "params": [
                {
                    "url": "/sys/login/user",
                    "data": {"user": self.username, "passwd": self.password},
                }
            ],
            "id": self.request_id,
        }
        self.request_id += 1

        try:
            response = self.session.post(self.base_url, json=login_payload)
            response.raise_for_status()
            response_json = response.json()
            
            if "session" not in response_json:
                raise FortiManagerAuthError(
                    f"Login failed: {response_json.get('result', [{}])[0].get('status', {}).get('message', 'Unknown error')}"
                )
            
            self.session_id = response_json["session"]
            logger.info("Successfully logged in to FortiManager")
        except requests.RequestException as e:
            raise FortiManagerAuthError(f"Login request failed: {str(e)}")

    def logout(self) -> None:
        """Logout from FortiManager API."""
        if not self.session_id:
            logger.warning("Not logged in, skipping logout")
            return

        logout_payload = {
            "method": "exec",
            "params": [{"url": "/sys/logout"}],
            "session": self.session_id,
            "id": self.request_id,
        }
        self.request_id += 1

        try:
            self.session.post(self.base_url, json=logout_payload)
            logger.info("Successfully logged out from FortiManager")
        except requests.RequestException as e:
            logger.warning(f"Logout request failed: {str(e)}")
        finally:
            self.session_id = None

    def _make_request(
        self, method: str, url: str, data: Optional[Dict] = None, params: Optional[Dict] = None
    ) -> Dict:
        """Make a request to the FortiManager API.

        Args:
            method: HTTP method (get, update, add, delete, etc.)
            url: API URL path
            data: Request data
            params: Request parameters

        Returns:
            API response as a dictionary

        Raises:
            FortiManagerAPIError: If the API request fails
        """
        if not self.session_id:
            self.login()

        payload = {
            "method": method,
            "params": [{"url": url, **({"data": data} if data else {})}],
            "session": self.session_id,
            "id": self.request_id,
        }
        self.request_id += 1

        try:
            response = self.session.post(self.base_url, json=payload, params=params)
            response.raise_for_status()
            response_json = response.json()
            
            result = response_json.get("result", [{}])[0]
            status = result.get("status", {})
            
            if status.get("code", -1) != 0:
                raise FortiManagerAPIError(
                    f"API request failed: {status.get('message', 'Unknown error')}"
                )
            
            return response_json
        except requests.RequestException as e:
            raise FortiManagerAPIError(f"API request failed: {str(e)}")

    def get_policies(self) -> List[Dict]:
        """Get all firewall policies.

        Returns:
            List of firewall policies
        """
        url = f"/pm/config/adom/{self.adom}/pkg/{self.package_name}/firewall/policy"
        response = self._make_request("get", url)
        return response.get("result", [{}])[0].get("data", [])

    def get_policy(self, policy_id: int) -> Dict:
        """Get a specific firewall policy.

        Args:
            policy_id: Policy ID

        Returns:
            Firewall policy
        """
        url = f"/pm/config/adom/{self.adom}/pkg/{self.package_name}/firewall/policy/{policy_id}"
        response = self._make_request("get", url)
        return response.get("result", [{}])[0].get("data", {})

    def update_policy(self, policy_id: int, data: Dict) -> Dict:
        """Update a firewall policy.

        Args:
            policy_id: Policy ID
            data: Policy data to update

        Returns:
            API response
        """
        url = f"/pm/config/adom/{self.adom}/pkg/{self.package_name}/firewall/policy/{policy_id}"
        return self._make_request("update", url, data)

    def update_policy_field(self, policy_id: int, field: str, data: List) -> Dict:
        """Update a specific field in a firewall policy.

        This method first clears the field and then adds the new data.

        Args:
            policy_id: Policy ID
            field: Field name
            data: New field data

        Returns:
            API response
        """
        # First clear the field
        url = f"/pm/config/adom/{self.adom}/pkg/{self.package_name}/firewall/policy/{policy_id}"
        self._make_request("update", url, {field: []})
        
        # Then add the new data if not empty
        if data:
            url = f"/pm/config/adom/{self.adom}/pkg/{self.package_name}/firewall/policy/{policy_id}/{field}"
            return self._make_request("add", url, data)
        return {"result": [{"status": {"code": 0, "message": "Field cleared"}}]}

    def __enter__(self) -> "FortiManagerClient":
        """Enter context manager."""
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        self.logout()
