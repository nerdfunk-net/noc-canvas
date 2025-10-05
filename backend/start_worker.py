"""
Celery worker startup script for NOC Canvas.

This script sets up the proper environment and starts a Celery worker.
You can run this directly or use the command line alternatives.
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(env_path)
    print(f"Loaded environment variables from {env_path}")
except ImportError:
    print("python-dotenv not available, environment variables must be set manually")

from app.services.background_jobs import celery_app

if __name__ == "__main__":
    # Start the Celery worker with prefork pool for Linux/Mac
    # This allows the worker to remain responsive to control commands even when tasks are running
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=4',  # 4 worker processes for parallel task execution
        '--pool=prefork',   # Prefork pool keeps control thread responsive
    ])
