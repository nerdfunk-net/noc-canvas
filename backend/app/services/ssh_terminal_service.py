"""
SSH Terminal Service for managing interactive SSH sessions via WebSocket.

This service manages SSH connections to network devices using paramiko,
allowing real-time terminal interaction through WebSocket connections.
"""

import asyncio
import logging
import threading
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import paramiko
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.credential import UserCredential, CredentialPurpose, decrypt_password

logger = logging.getLogger(__name__)


@dataclass
class SSHSession:
    """Represents an active SSH session."""
    session_id: str
    device_id: str
    device_name: str
    device_ip: str
    username: str
    ssh_client: paramiko.SSHClient
    ssh_channel: paramiko.Channel
    created_at: datetime
    last_activity: datetime
    is_active: bool = True


class SSHTerminalService:
    """Service for managing SSH terminal sessions."""

    def __init__(self):
        self.sessions: Dict[str, SSHSession] = {}
        self.session_timeout = 1800  # 30 minutes in seconds
        self._cleanup_task = None
        logger.info("SSH Terminal Service initialized")

    async def create_session(
        self,
        session_id: str,
        device_id: str,
        device_name: str,
        device_ip: str,
        network_driver: str,
        username: str,
    ) -> Dict[str, Any]:
        """
        Create a new SSH session to a device.

        Args:
            session_id: Unique identifier for this session
            device_id: Device ID from Nautobot
            device_name: Name of the device
            device_ip: IP address of the device
            network_driver: Network driver type (not used for raw SSH but kept for compatibility)
            username: Username of the authenticated user

        Returns:
            Dict with success status and session info or error message
        """
        try:
            logger.info(
                f"🔐 Creating SSH session {session_id} to device {device_name} ({device_ip}) for user {username}"
            )

            # Get credentials
            logger.info(f"🔍 Fetching credentials for user: {username}")
            credentials = await self._get_credentials(username)
            if not credentials:
                logger.error(f"❌ No credentials found for user {username}")
                return {
                    "success": False,
                    "error": "No valid credentials found. Please add SSH or TACACS credentials in Settings.",
                }

            logger.info(f"✅ Found {credentials['type'].upper()} credentials: {credentials['name']}")
            logger.info(f"   SSH Username: {credentials['username']}")

            # Create SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to device
            try:
                logger.info(f"🔌 Connecting to {device_ip} as {credentials['username']}...")
                ssh_client.connect(
                    hostname=device_ip,
                    username=credentials["username"],
                    password=credentials["password"],
                    timeout=10,
                    look_for_keys=False,
                    allow_agent=False,
                )
                logger.info(f"✅ SSH connection established to {device_ip}")
            except paramiko.AuthenticationException as e:
                logger.error(f"Authentication failed for {device_name}: {str(e)}")
                return {
                    "success": False,
                    "error": "Authentication failed. Please check your credentials in Settings.",
                }
            except paramiko.SSHException as e:
                logger.error(f"SSH connection failed for {device_name}: {str(e)}")
                return {
                    "success": False,
                    "error": f"SSH connection failed: {str(e)}",
                }
            except Exception as e:
                logger.error(f"Connection error for {device_name}: {str(e)}")
                return {
                    "success": False,
                    "error": f"Connection error: {str(e)}",
                }

            # Open an interactive shell channel with PTY
            try:
                channel = ssh_client.invoke_shell(
                    term="xterm-256color",
                    width=80,
                    height=24,
                )
                channel.settimeout(0.1)  # Non-blocking reads
            except Exception as e:
                logger.error(f"Failed to open shell channel: {str(e)}")
                ssh_client.close()
                return {
                    "success": False,
                    "error": f"Failed to open shell: {str(e)}",
                }

            # Create session object
            session = SSHSession(
                session_id=session_id,
                device_id=device_id,
                device_name=device_name,
                device_ip=device_ip,
                username=username,
                ssh_client=ssh_client,
                ssh_channel=channel,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                is_active=True,
            )

            # Store session
            self.sessions[session_id] = session

            logger.info(
                f"SSH session {session_id} created successfully for device {device_name}"
            )

            return {
                "success": True,
                "session_id": session_id,
                "device_name": device_name,
                "device_ip": device_ip,
            }

        except Exception as e:
            logger.error(f"Unexpected error creating SSH session: {str(e)}")
            logger.exception("Full exception:")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            }

    async def send_input(self, session_id: str, data: str) -> bool:
        """
        Send user input to the SSH channel.

        Args:
            session_id: Session identifier
            data: Data to send to the device

        Returns:
            True if successful, False otherwise
        """
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            logger.warning(f"Session {session_id} not found or inactive")
            return False

        try:
            # Send data to SSH channel
            session.ssh_channel.send(data)
            session.last_activity = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Error sending data to session {session_id}: {str(e)}")
            return False

    async def read_output(self, session_id: str) -> Optional[str]:
        """
        Read output from the SSH channel.

        Args:
            session_id: Session identifier

        Returns:
            Output data as string, or None if no data or error
        """
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return None

        try:
            # Check if channel is closed
            if session.ssh_channel.closed or session.ssh_channel.eof_received:
                logger.info(f"SSH channel closed for session {session_id}")
                session.is_active = False
                return None

            # Check if there's data available
            if session.ssh_channel.recv_ready():
                data = session.ssh_channel.recv(4096)
                session.last_activity = datetime.now()
                return data.decode("utf-8", errors="replace")
            return None
        except Exception as e:
            logger.error(f"Error reading from session {session_id}: {str(e)}")
            session.is_active = False
            return None

    async def resize_terminal(self, session_id: str, width: int, height: int) -> bool:
        """
        Resize the terminal window.

        Args:
            session_id: Session identifier
            width: Terminal width in characters
            height: Terminal height in characters

        Returns:
            True if successful, False otherwise
        """
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return False

        try:
            session.ssh_channel.resize_pty(width=width, height=height)
            logger.debug(f"Resized terminal for session {session_id}: {width}x{height}")
            return True
        except Exception as e:
            logger.error(f"Error resizing terminal for session {session_id}: {str(e)}")
            return False

    async def close_session(self, session_id: str) -> bool:
        """
        Close an SSH session.

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return False

        try:
            logger.info(f"Closing SSH session {session_id}")
            session.is_active = False

            # Close channel and client
            if session.ssh_channel:
                session.ssh_channel.close()
            if session.ssh_client:
                session.ssh_client.close()

            # Remove from sessions dict
            del self.sessions[session_id]

            logger.info(f"SSH session {session_id} closed successfully")
            return True
        except Exception as e:
            logger.error(f"Error closing session {session_id}: {str(e)}")
            return False

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "device_id": session.device_id,
            "device_name": session.device_name,
            "device_ip": session.device_ip,
            "username": session.username,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "is_active": session.is_active,
        }

    async def cleanup_inactive_sessions(self):
        """Clean up sessions that have been inactive for too long."""
        now = datetime.now()
        sessions_to_remove = []

        for session_id, session in self.sessions.items():
            if now - session.last_activity > timedelta(seconds=self.session_timeout):
                logger.info(
                    f"Session {session_id} inactive for {self.session_timeout}s, closing..."
                )
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            await self.close_session(session_id)

        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} inactive sessions")

    async def _get_credentials(self, username: str) -> Optional[Dict[str, str]]:
        """Get user credentials from database, prioritizing SSH over TACACS for terminal access."""
        try:
            logger.debug(f"Getting credentials for user: {username}")
            db: Session = next(get_db())

            # For terminal access, try SSH first (more appropriate for interactive sessions)
            ssh_credential = (
                db.query(UserCredential)
                .filter(
                    UserCredential.owner == username,
                    UserCredential.purpose == CredentialPurpose.SSH,
                )
                .first()
            )

            if ssh_credential:
                logger.debug(f"Found SSH credential: {ssh_credential.name}")
                decrypted_password = decrypt_password(ssh_credential.encrypted_password)
                return {
                    "username": ssh_credential.username,
                    "password": decrypted_password,
                    "name": ssh_credential.name,
                    "type": "ssh",
                }

            # Fall back to TACACS if no SSH credentials
            tacacs_credential = (
                db.query(UserCredential)
                .filter(
                    UserCredential.owner == username,
                    UserCredential.purpose == CredentialPurpose.TACACS,
                )
                .first()
            )

            if tacacs_credential:
                logger.debug(f"Found TACACS credential: {tacacs_credential.name}")
                decrypted_password = decrypt_password(
                    tacacs_credential.encrypted_password
                )
                return {
                    "username": tacacs_credential.username,
                    "password": decrypted_password,
                    "name": tacacs_credential.name,
                    "type": "tacacs",
                }

            logger.warning(f"No SSH or TACACS credentials found for user {username}")
            return None

        except Exception as e:
            logger.error(f"Error getting credentials for user {username}: {str(e)}")
            return None
        finally:
            if "db" in locals():
                db.close()


# Global service instance
ssh_terminal_service = SSHTerminalService()
