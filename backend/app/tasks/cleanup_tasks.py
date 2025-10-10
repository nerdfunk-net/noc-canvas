"""
Cleanup tasks.

This module contains Celery tasks for cleaning up old data and maintaining database health.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def register_tasks(celery_app):
    """Register cleanup tasks with the Celery app."""

    @celery_app.task(bind=True, name='app.tasks.cleanup_tasks.cleanup_old_data')
    def cleanup_old_data(self):
        """
        Clean up expired and old data from the database.
        
        This task performs a comprehensive cleanup of:
        1. Expired periodic tasks (tasks past their expiry date)
        2. Old task executions (older than 30 days)
        3. Old Celery results (older than 7 days)
        4. Orphaned task changes (from deleted tasks)
        
        The cleanup is performed in stages with progress tracking.
        
        Returns:
            Dictionary with cleanup statistics
        """
        from ..services.database import engine
        from celery_sqlalchemy_scheduler.models import PeriodicTask, PeriodicTaskChanged
        from celery.backends.database.models import Task as CeleryTask
        from ..models.task_execution import TaskExecution

        try:
            self.update_state(state="PROGRESS", meta={"current": 0, "total": 100})
            
            # Initialize cleanup statistics
            stats = {
                "expired_tasks_deleted": 0,
                "old_executions_deleted": 0,
                "old_celery_results_deleted": 0,
                "orphaned_changes_deleted": 0,
                "errors": []
            }
            
            # Stage 1: Delete expired periodic tasks
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 10,
                    "total": 100,
                    "status": "Cleaning up expired periodic tasks",
                },
            )
            
            try:
                with Session(engine) as session:
                    current_time = datetime.utcnow()
                    
                    # Find and delete expired tasks
                    expired_tasks = session.query(PeriodicTask).filter(
                        PeriodicTask.expires != None,
                        PeriodicTask.expires < current_time
                    ).all()
                    
                    for task in expired_tasks:
                        logger.info(f"Deleting expired task: {task.name} (expired: {task.expires})")
                        session.delete(task)
                    
                    session.commit()
                    stats["expired_tasks_deleted"] = len(expired_tasks)
                    
            except Exception as e:
                error_msg = f"Error deleting expired tasks: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
            
            # Stage 2: Clean up old task executions (older than 30 days)
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 35,
                    "total": 100,
                    "status": "Cleaning up old task executions",
                },
            )
            
            try:
                with Session(engine) as session:
                    cutoff_date = datetime.utcnow() - timedelta(days=30)
                    
                    # Delete old task execution records
                    deleted_count = session.query(TaskExecution).filter(
                        TaskExecution.timestamp < cutoff_date
                    ).delete()
                    
                    session.commit()
                    stats["old_executions_deleted"] = deleted_count
                    logger.info(f"Deleted {deleted_count} old task execution records")
                    
            except Exception as e:
                error_msg = f"Error deleting old task executions: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
            
            # Stage 3: Clean up old Celery results (older than 7 days)
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 60,
                    "total": 100,
                    "status": "Cleaning up old Celery results",
                },
            )
            
            try:
                with Session(engine) as session:
                    cutoff_date = datetime.utcnow() - timedelta(days=7)
                    
                    # Delete old Celery task results
                    deleted_count = session.query(CeleryTask).filter(
                        CeleryTask.date_done != None,
                        CeleryTask.date_done < cutoff_date
                    ).delete()
                    
                    session.commit()
                    stats["old_celery_results_deleted"] = deleted_count
                    logger.info(f"Deleted {deleted_count} old Celery result records")
                    
            except Exception as e:
                error_msg = f"Error deleting old Celery results: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
            
            # Stage 4: Clean up orphaned task changes
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 85,
                    "total": 100,
                    "status": "Cleaning up orphaned task changes",
                },
            )
            
            try:
                with Session(engine) as session:
                    # Get all valid task IDs
                    valid_task_ids = [t.id for t in session.query(PeriodicTask.id).all()]
                    
                    # Delete changes for tasks that no longer exist
                    orphaned_changes = session.query(PeriodicTaskChanged).filter(
                        ~PeriodicTaskChanged.id.in_(valid_task_ids)
                    ).delete(synchronize_session=False)
                    
                    session.commit()
                    stats["orphaned_changes_deleted"] = orphaned_changes
                    logger.info(f"Deleted {orphaned_changes} orphaned task change records")
                    
            except Exception as e:
                error_msg = f"Error deleting orphaned task changes: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
            
            # Final status
            self.update_state(state="PROGRESS", meta={"current": 100, "total": 100})
            
            # Log summary
            logger.info(f"Cleanup completed: {stats}")
            
            return {
                "status": "completed",
                "message": "Cleanup completed successfully",
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_data task: {str(e)}")
            self.update_state(
                state="FAILURE",
                meta={
                    "error": str(e),
                    "status": "Failed to clean up old data",
                },
            )
            raise

    return {
        'cleanup_old_data': cleanup_old_data,
    }
