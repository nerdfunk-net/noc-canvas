"""
Celery worker startup script for NOC Canvas.
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.background_jobs import celery_app

if __name__ == "__main__":
    celery_app.start()
