"""
Test tasks.

This module contains Celery tasks for testing and verification purposes.
"""

import logging
import time

logger = logging.getLogger(__name__)


def register_tasks(celery_app):
    """Register test tasks with the Celery app."""

    @celery_app.task(bind=True, name="app.tasks.test_tasks.test_background_task")
    def test_background_task(self, duration: int = 10):
        """
        Test task that simulates a long-running background job.

        This task is useful for testing:
        - Task execution and state updates
        - Progress tracking
        - Error handling
        - Task scheduling

        Args:
            duration: How many seconds the task should run for

        Returns:
            Dictionary with test results
        """
        try:
            # Simulate work with progress updates
            for i in range(duration):
                time.sleep(1)
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": duration,
                        "status": f"Processing step {i + 1} of {duration}",
                    },
                )
                logger.info(f"Test task progress: {i + 1}/{duration}")

            logger.info("Test background task completed successfully")

            return {
                "status": "completed",
                "message": f"Test task completed after {duration} seconds",
                "duration": duration,
            }

        except Exception as e:
            logger.error(f"Error in test_background_task: {str(e)}")
            self.update_state(
                state="FAILURE",
                meta={
                    "error": str(e),
                    "status": "Test task failed",
                },
            )
            raise

    return {
        "test_background_task": test_background_task,
    }
