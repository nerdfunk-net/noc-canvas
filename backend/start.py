"""
Startup script for NOC Canvas backend.
"""

import uvicorn
import sys
import os
import logging

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure root logging first
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,  # This forces reconfiguration even if logging was already configured
)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(env_path)
    print(f"Loaded environment variables from {env_path}")
except ImportError:
    print("python-dotenv not available, environment variables must be set manually")

if __name__ == "__main__":
    # Configure uvicorn logging to use our logging configuration
    uvicorn_config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
        access_log=True,
        use_colors=True,
    )

    server = uvicorn.Server(uvicorn_config)
    server.run()
