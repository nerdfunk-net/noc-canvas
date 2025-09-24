"""
Device communication service for connecting to network devices using netmiko.
"""

import logging
import time
from typing import Dict, Any, Optional
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
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
        username: str
    ) -> Dict[str, Any]:
        """Execute a command on a network device."""
        start_time = time.time()

        try:
            # Convert Pydantic model to dict if needed
            if hasattr(device_info, 'model_dump'):
                device_dict = device_info.model_dump()
                logger.debug(f"Converted DeviceConnectionInfo to dict: {device_dict}")
            else:
                device_dict = device_info

            # Get device credentials
            device_config = await self._get_device_config(device_dict, username)

            logger.info(f"Connecting to device {device_dict['name']} ({device_dict['primary_ip']}) to execute: {command}")

            # Create netmiko connection
            with ConnectHandler(**device_config) as connection:
                # Send command and get output
                output = connection.send_command(
                    command,
                    delay_factor=self.global_delay_factor,
                    max_loops=self.max_loops
                )

                execution_time = time.time() - start_time

                logger.info(f"Successfully executed command on {device_dict['name']} in {execution_time:.2f}s")

                return {
                    "success": True,
                    "output": output,
                    "execution_time": execution_time
                }

        except NetmikoTimeoutException as e:
            execution_time = time.time() - start_time
            error_msg = f"Timeout connecting to device {device_dict.get('name', 'unknown')}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time
            }

        except NetmikoAuthenticationException as e:
            execution_time = time.time() - start_time
            error_msg = f"Authentication failed for device {device_dict.get('name', 'unknown')}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error executing command on device {device_dict.get('name', 'unknown')}: {str(e)}"
            logger.error(error_msg)
            logger.exception("Full exception details:")
            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time
            }

    async def _get_device_config(self, device_info: Dict[str, Any], username: str) -> Dict[str, Any]:
        """Get device connection configuration including credentials."""
        # Get SSH credentials from database
        ssh_credential = await self._get_ssh_credential(username)

        if not ssh_credential:
            raise Exception(f"No SSH credentials found for user {username}. Please add SSH credentials in Settings.")

        device_config = {
            'device_type': self._map_platform_to_netmiko_type(device_info['network_driver']),
            'host': device_info['primary_ip'],
            'username': ssh_credential['username'],
            'password': ssh_credential['password'],
            'timeout': self.timeout,
            'global_delay_factor': self.global_delay_factor,
        }

        # Add optional SSH key if configured
        if hasattr(settings, 'device_ssh_key_file') and settings.device_ssh_key_file:
            device_config['use_keys'] = True
            device_config['key_file'] = settings.device_ssh_key_file

        # Add port if non-standard
        if hasattr(settings, 'device_default_port') and settings.device_default_port:
            device_config['port'] = settings.device_default_port

        return device_config

    async def _get_ssh_credential(self, username: str) -> Optional[Dict[str, str]]:
        """Get SSH credentials for the user from database."""
        try:
            logger.debug(f"Getting SSH credentials for user: {username}")
            # Get database session
            db: Session = next(get_db())

            # Query for SSH credentials for this user
            credential = (
                db.query(UserCredential)
                .filter(
                    UserCredential.owner == username,
                    UserCredential.purpose == CredentialPurpose.SSH
                )
                .first()
            )

            if credential:
                logger.debug(f"Found SSH credential: {credential.name} for user {username}")
                # Decrypt password and return
                decrypted_password = decrypt_password(credential.encrypted_password)
                return {
                    'username': credential.username,
                    'password': decrypted_password,
                    'name': credential.name
                }

            logger.warning(f"No SSH credentials found for user {username}")
            return None

        except Exception as e:
            logger.error(f"Error getting SSH credentials for user {username}: {str(e)}")
            logger.exception("Full exception details:")
            return None
        finally:
            if 'db' in locals():
                db.close()

    def _map_platform_to_netmiko_type(self, network_driver: str) -> str:
        """Map Nautobot platform network_driver to netmiko device_type."""
        # Common platform mappings
        driver_mapping = {
            'cisco_ios': 'cisco_ios',
            'cisco_xe': 'cisco_xe',
            'cisco_xr': 'cisco_xr',
            'cisco_nxos': 'cisco_nxos',
            'cisco_asa': 'cisco_asa',
            'juniper_junos': 'juniper_junos',
            'arista_eos': 'arista_eos',
            'hp_procurve': 'hp_procurve',
            'hp_comware': 'hp_comware',
            'fortinet': 'fortinet',
            'palo_alto_panos': 'paloalto_panos',
            'f5_tmsh': 'f5_tmsh',
            'checkpoint_gaia': 'checkpoint_gaia',
            'linux': 'linux',
        }

        # Return mapped type or default to cisco_ios
        mapped_type = driver_mapping.get(network_driver.lower(), 'cisco_ios')
        logger.debug(f"Mapped network_driver '{network_driver}' to netmiko device_type '{mapped_type}'")
        return mapped_type

    async def get_command_by_id(self, command_id: str, username: str) -> Optional[str]:
        """Get command string by command ID from database or predefined commands."""
        # TODO: Implement command management system with database storage
        # For now, return some predefined commands based on ID

        predefined_commands = {
            'version': 'show version',
            'interfaces': 'show interfaces',
            'interface_status': 'show interfaces status',
            'vlan': 'show vlan',
            'mac_table': 'show mac address-table',
            'arp_table': 'show arp',
            'spanning_tree': 'show spanning-tree',
            'log': 'show log',
            'inventory': 'show inventory',
            'environment': 'show environment',
            'users': 'show users',
            'processes': 'show processes',
            'memory': 'show memory',
            'cpu': 'show cpu',
        }

        command = predefined_commands.get(command_id)
        if command:
            logger.debug(f"Found predefined command for ID '{command_id}': {command}")
        else:
            logger.warning(f"Command ID '{command_id}' not found in predefined commands")

        return command

    async def test_device_connection(
        self,
        device_info,  # Can be DeviceConnectionInfo or Dict
        username: str
    ) -> Dict[str, Any]:
        """Test connection to a network device."""
        try:
            # Convert Pydantic model to dict if needed
            if hasattr(device_info, 'model_dump'):
                device_dict = device_info.model_dump()
            else:
                device_dict = device_info

            device_config = await self._get_device_config(device_dict, username)

            logger.info(f"Testing connection to device {device_dict['name']} ({device_dict['primary_ip']})")

            with ConnectHandler(**device_config) as connection:
                # Send a simple command to test the connection
                output = connection.send_command("show version | include uptime", delay_factor=1)

                return {
                    "success": True,
                    "message": "Connection successful",
                    "test_output": output[:200]  # First 200 chars for verification
                }

        except Exception as e:
            error_msg = f"Connection test failed for device {device_dict.get('name', 'unknown')}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }


# Global service instance
device_communication_service = DeviceCommunicationService()