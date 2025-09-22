"""
Celery worker startup script for NOC Canvas.

This script sets up the proper environment and starts a Celery worker.
You can run this directly or use the command line alternatives.
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.background_jobs import celery_app

if __name__ == "__main__":
    # Start the Celery worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--pool=solo',  # Use solo pool for Windows compatibility, remove for Linux/Mac
    ])
