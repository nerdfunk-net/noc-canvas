"""
Device communication service for connecting to network devices using netmiko.
"""

import logging
import time
from typing import Dict, Any, Optional
from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.database import get_db
from ..models.credential import UserCredential, CredentialPurpose, decrypt_password

logger = logging.getLogger(__name__)


class DeviceCommunicationService:
    """Service for communicating with network devices using netmiko."""

    def __init__(self):
        self.timeout = 30
        self.global_delay_factor = 1
        self.max_loops = 150

    async def execute_command(
        self,
        device_info,  # Can be DeviceConnectionInfo or Dict
        command: str,
        username: str,
        parser: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a command on a network device."""
        start_time = time.time()

        try:
            # Convert Pydantic model to dict if needed
            if hasattr(device_info, "model_dump"):
                device_dict = device_info.model_dump()
                logger.debug(f"Converted DeviceConnectionInfo to dict: {device_dict}")
            else:
                device_dict = device_info

            # Get device credentials
            device_config = await self._get_device_config(device_dict, username)

            logger.info(
                f"Connecting to device {device_dict['name']} ({device_dict['primary_ip']}) to execute: {command}"
            )

            # Create netmiko connection
            with ConnectHandler(**device_config) as connection:
                # Send command and get output
                if parser and parser.upper() in ["TEXTFSM", "TTP"]:
                    # Use netmiko's structured output parsing
                    output = connection.send_command(
                        command,
                        delay_factor=self.global_delay_factor,
                        max_loops=self.max_loops,
                        use_textfsm=True if parser.upper() == "TEXTFSM" else False,
                        use_ttp=True if parser.upper() == "TTP" else False,
                    )
                    parsed_output = True
                else:
                    # Send command without parsing
                    output = connection.send_command(
                        command,
                        delay_factor=self.global_delay_factor,
                        max_loops=self.max_loops,
                    )
                    parsed_output = False

                execution_time = time.time() - start_time

                logger.info(
                    f"Successfully executed command on {device_dict['name']} in {execution_time:.2f}s (parser: {parser or 'none'})"
                )

                return {
                    "success": True,
                    "output": output,
                    "parsed": parsed_output,
                    "parser_used": parser,
                    "execution_time": execution_time,
                }

        except NetmikoTimeoutException as e:
            execution_time = time.time() - start_time
            error_msg = f"Timeout connecting to device {device_dict.get('name', 'unknown')}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "timeout",
                "execution_time": execution_time,
            }

        except NetmikoAuthenticationException as e:
            execution_time = time.time() - start_time
            error_msg = "Login failed. Please check your credentials in Settings."
            logger.error(
                f"Authentication failed for device {device_dict.get('name', 'unknown')}: {str(e)}"
            )
            return {
                "success": False,
                "error": error_msg,
                "error_type": "authentication_failed",
                "execution_time": execution_time,
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_str = str(e)

            # Handle specific error cases
            if "No valid credentials found" in error_str:
                error_msg = "No valid credentials found. Please add TACACS or SSH credentials in Settings."
                error_type = "no_credentials"
            else:
                error_msg = f"Error executing command on device {device_dict.get('name', 'unknown')}: {error_str}"
                error_type = "general_error"

            logger.error(error_msg)
            logger.exception("Full exception details:")
            return {
                "success": False,
                "error": error_msg,
                "error_type": error_type,
                "execution_time": execution_time,
            }

    async def _get_device_config(
        self, device_info: Dict[str, Any], username: str
    ) -> Dict[str, Any]:
        """Get device connection configuration including credentials."""
        # First try to get TACACS credentials, then fall back to SSH
        credential = await self._get_user_credential(username)

        if not credential:
            raise Exception(
                "No valid credentials found. Please add TACACS or SSH credentials in Settings."
            )

        device_config = {
            "device_type": self._map_platform_to_netmiko_type(
                device_info["network_driver"]
            ),
            "host": device_info["primary_ip"],
            "username": credential["username"],
            "password": credential["password"],
            "timeout": self.timeout,
            "global_delay_factor": self.global_delay_factor,
        }

        # Add optional SSH key if configured
        if hasattr(settings, "device_ssh_key_file") and settings.device_ssh_key_file:
            device_config["use_keys"] = True
            device_config["key_file"] = settings.device_ssh_key_file

        # Add port if non-standard
        if hasattr(settings, "device_default_port") and settings.device_default_port:
            device_config["port"] = settings.device_default_port

        return device_config

    async def _get_user_credential(self, username: str) -> Optional[Dict[str, str]]:
        """Get user credentials from database, prioritizing TACACS over SSH."""
        try:
            logger.debug(f"Getting credentials for user: {username}")
            # Get database session
            db: Session = next(get_db())

            # First try to get TACACS credentials
            tacacs_credential = (
                db.query(UserCredential)
                .filter(
                    UserCredential.owner == username,
                    UserCredential.purpose == CredentialPurpose.TACACS,
                )
                .first()
            )

            if tacacs_credential:
                logger.debug(
                    f"Found TACACS credential: {tacacs_credential.name} for user {username}"
                )
                # Decrypt password and return
                decrypted_password = decrypt_password(
                    tacacs_credential.encrypted_password
                )
                return {
                    "username": tacacs_credential.username,
                    "password": decrypted_password,
                    "name": tacacs_credential.name,
                    "type": "tacacs",
                }

            # If no TACACS credentials found, try SSH credentials
            logger.debug(
                f"No TACACS credentials found for user {username}, trying SSH credentials"
            )
            ssh_credential = (
                db.query(UserCredential)
                .filter(
                    UserCredential.owner == username,
                    UserCredential.purpose == CredentialPurpose.SSH,
                )
                .first()
            )

            if ssh_credential:
                logger.debug(
                    f"Found SSH credential: {ssh_credential.name} for user {username}"
                )
                # Decrypt password and return
                decrypted_password = decrypt_password(ssh_credential.encrypted_password)
                return {
                    "username": ssh_credential.username,
                    "password": decrypted_password,
                    "name": ssh_credential.name,
                    "type": "ssh",
                }

            logger.warning(f"No TACACS or SSH credentials found for user {username}")
            return None

        except Exception as e:
            logger.error(f"Error getting credentials for user {username}: {str(e)}")
            logger.exception("Full exception details:")
            return None
        finally:
            if "db" in locals():
                db.close()

    def _map_platform_to_netmiko_type(self, network_driver: str) -> str:
        """Map Nautobot platform network_driver to netmiko device_type."""
        # Common platform mappings
        driver_mapping = {
            "cisco_ios": "cisco_ios",
            "cisco_xe": "cisco_xe",
            "cisco_xr": "cisco_xr",
            "cisco_nxos": "cisco_nxos",
            "cisco_asa": "cisco_asa",
            "juniper_junos": "juniper_junos",
            "arista_eos": "arista_eos",
            "hp_procurve": "hp_procurve",
            "hp_comware": "hp_comware",
            "fortinet": "fortinet",
            "palo_alto_panos": "paloalto_panos",
            "f5_tmsh": "f5_tmsh",
            "checkpoint_gaia": "checkpoint_gaia",
            "linux": "linux",
        }

        # Return mapped type or default to cisco_ios
        mapped_type = driver_mapping.get(network_driver.lower(), "cisco_ios")
        logger.debug(
            f"Mapped network_driver '{network_driver}' to netmiko device_type '{mapped_type}'"
        )
        return mapped_type

    async def test_device_connection(
        self,
        device_info,  # Can be DeviceConnectionInfo or Dict
        username: str,
    ) -> Dict[str, Any]:
        """Test connection to a network device."""
        try:
            # Convert Pydantic model to dict if needed
            if hasattr(device_info, "model_dump"):
                device_dict = device_info.model_dump()
            else:
                device_dict = device_info

            device_config = await self._get_device_config(device_dict, username)

            logger.info(
                f"Testing connection to device {device_dict['name']} ({device_dict['primary_ip']})"
            )

            with ConnectHandler(**device_config) as connection:
                # Send a simple command to test the connection
                output = connection.send_command(
                    "show version | include uptime", delay_factor=1
                )

                return {
                    "success": True,
                    "message": "Connection successful",
                    "test_output": output[:200],  # First 200 chars for verification
                }

        except Exception as e:
            error_msg = f"Connection test failed for device {device_dict.get('name', 'unknown')}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}


# Global service instance
device_communication_service = DeviceCommunicationService()
