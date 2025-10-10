"""
SSH Terminal WebSocket API endpoint.

Provides WebSocket connection for interactive SSH terminal sessions to network devices.
"""

import asyncio
import json
import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional

from ..core.security import get_current_user_ws
from ..services.ssh_terminal_service import ssh_terminal_service
from ..services.nautobot import nautobot_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/ssh/{device_id}")
async def ssh_terminal_websocket(
    websocket: WebSocket,
    device_id: str,
    token: str = Query(...),
):
    """
    WebSocket endpoint for SSH terminal access to a device.

    Args:
        websocket: WebSocket connection
        device_id: Device ID from Nautobot
        token: Authentication token (passed as query parameter)

    Message Format (Client -> Server):
        {
            "type": "input",
            "data": "command text or key sequence"
        }
        {
            "type": "resize",
            "cols": 80,
            "rows": 24
        }

    Message Format (Server -> Client):
        {
            "type": "output",
            "data": "terminal output"
        }
        {
            "type": "connected",
            "device_name": "device1",
            "device_ip": "10.0.0.1"
        }
        {
            "type": "error",
            "message": "error description"
        }
        {
            "type": "disconnected"
        }
    """
    session_id = None

    try:
        # Accept WebSocket connection
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for device {device_id}")

        # Authenticate user using token
        try:
            user = await get_current_user_ws(token)
            username = user.get("username") if isinstance(user, dict) else user.username
            logger.info(f"User {username} authenticated for SSH terminal to device {device_id}")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed. Please log in again."
            })
            await websocket.close(code=1008)  # Policy violation
            return

        # Get device information from Nautobot
        try:
            logger.info(f"🔍 Fetching device info from Nautobot for device_id: {device_id}")
            device_data = await nautobot_service.get_device(device_id, username=username)
            if not device_data:
                logger.error(f"❌ Device {device_id} not found in Nautobot")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Device {device_id} not found"
                })
                await websocket.close(code=1008)
                return

            # Extract device info
            device_name = device_data.get("name", "Unknown")
            logger.info(f"✅ Found device: {device_name}")

            primary_ip4 = device_data.get("primary_ip4")
            logger.debug(f"   Primary IP4 data: {primary_ip4}")

            if not primary_ip4 or not primary_ip4.get("address"):
                logger.error(f"❌ Device {device_name} does not have a primary IP address configured")
                await websocket.send_json({
                    "type": "error",
                    "message": "Device does not have a primary IP address configured"
                })
                await websocket.close(code=1008)
                return

            device_ip = primary_ip4["address"].split("/")[0]
            logger.info(f"📍 Device IP address: {device_ip}")

            # Get platform/network driver
            platform_info = device_data.get("platform")
            network_driver = platform_info.get("network_driver", "cisco_ios") if platform_info else "cisco_ios"
            logger.info(f"🖥️  Platform/Driver: {platform_info.get('name') if platform_info else 'Unknown'} / {network_driver}")

        except Exception as e:
            logger.error(f"❌ Error getting device info: {str(e)}")
            logger.exception("Full exception:")
            await websocket.send_json({
                "type": "error",
                "message": f"Failed to get device information: {str(e)}"
            })
            await websocket.close(code=1011)  # Internal error
            return

        # Create SSH session
        session_id = str(uuid.uuid4())
        logger.info(f"🔐 Creating SSH session {session_id}")
        logger.info(f"   Device: {device_name} ({device_ip})")
        logger.info(f"   User: {username}")

        result = await ssh_terminal_service.create_session(
            session_id=session_id,
            device_id=device_id,
            device_name=device_name,
            device_ip=device_ip,
            network_driver=network_driver,
            username=username,
        )

        logger.info(f"📊 SSH session creation result: {result.get('success')}")

        if not result["success"]:
            logger.error(f"Failed to create SSH session: {result.get('error')}")
            await websocket.send_json({
                "type": "error",
                "message": result.get("error", "Failed to connect to device")
            })
            await websocket.close(code=1011)
            return

        # Send connection success message
        await websocket.send_json({
            "type": "connected",
            "device_name": device_name,
            "device_ip": device_ip,
        })
        logger.info(f"SSH session {session_id} established for device {device_name}")

        # Start output reading task
        async def read_ssh_output():
            """Continuously read from SSH channel and send to WebSocket."""
            while True:
                try:
                    output = await ssh_terminal_service.read_output(session_id)
                    if output:
                        await websocket.send_json({
                            "type": "output",
                            "data": output
                        })

                    # Check if SSH channel is closed
                    session_info = ssh_terminal_service.get_session_info(session_id)
                    if session_info and not session_info.get("is_active"):
                        logger.info(f"SSH channel closed for session {session_id}")
                        # Send disconnected message with reason
                        await websocket.send_json({
                            "type": "disconnected",
                            "reason": "normal",
                            "message": "SSH session ended"
                        })
                        break

                    await asyncio.sleep(0.05)  # 50ms polling interval
                except Exception as e:
                    logger.error(f"Error reading SSH output: {str(e)}")
                    # Send disconnected message with error
                    try:
                        await websocket.send_json({
                            "type": "disconnected",
                            "reason": "error",
                            "message": str(e)
                        })
                    except:
                        pass
                    break

        # Start background task for reading output
        output_task = asyncio.create_task(read_ssh_output())

        try:
            # Main loop: receive input from WebSocket and send to SSH
            while True:
                # Receive message from WebSocket
                message = await websocket.receive_text()

                try:
                    data = json.loads(message)
                    msg_type = data.get("type")

                    if msg_type == "input":
                        # Send user input to SSH session
                        input_data = data.get("data", "")
                        success = await ssh_terminal_service.send_input(session_id, input_data)
                        if not success:
                            logger.warning(f"Failed to send input to session {session_id}")

                    elif msg_type == "resize":
                        # Resize terminal
                        cols = data.get("cols", 80)
                        rows = data.get("rows", 24)
                        await ssh_terminal_service.resize_terminal(session_id, cols, rows)

                    else:
                        logger.warning(f"Unknown message type: {msg_type}")

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket loop: {str(e)}")
        finally:
            # Cancel output reading task
            output_task.cancel()
            try:
                await output_task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(f"Unexpected error in SSH terminal WebSocket: {str(e)}")
        logger.exception("Full exception:")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Unexpected error: {str(e)}"
            })
        except:
            pass

    finally:
        # Clean up session
        if session_id:
            logger.info(f"Cleaning up SSH session {session_id}")
            await ssh_terminal_service.close_session(session_id)

        # Close WebSocket if still open
        try:
            await websocket.close()
        except:
            pass

        logger.info(f"SSH terminal WebSocket closed for device {device_id}")
