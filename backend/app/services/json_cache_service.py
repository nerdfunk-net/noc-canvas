"""
JSON cache service for managing cached JSON data from device commands.
Provides methods to set, get, and delete cached JSON blobs.
"""

import logging
import json
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.device_cache import JSONBlobCache
from ..models.settings import AppSettings

logger = logging.getLogger(__name__)


class JSONCacheService:
    """Service for managing JSON blob cache data."""

    @staticmethod
    def set_cache(
        db: Session, device_id: str, command: str, json_data: str
    ) -> JSONBlobCache:
        """
        Set or update a JSON cache entry for a device command.
        If an entry exists, it will be updated with new data.

        Args:
            db: Database session
            device_id: Device UUID
            command: Command that was executed
            json_data: JSON string data to cache

        Returns:
            JSONBlobCache: The created or updated cache entry
        """
        # Check if entry already exists
        existing = (
            db.query(JSONBlobCache)
            .filter(
                and_(
                    JSONBlobCache.device_id == device_id,
                    JSONBlobCache.command == command,
                )
            )
            .first()
        )

        if existing:
            # Update existing entry
            existing.json_data = json_data
            db.commit()
            db.refresh(existing)
            logger.info(
                f"Updated JSON cache for device {device_id}, command: {command}"
            )
            return existing
        else:
            # Create new entry
            cache_entry = JSONBlobCache(
                device_id=device_id, command=command, json_data=json_data
            )
            db.add(cache_entry)
            db.commit()
            db.refresh(cache_entry)
            logger.info(
                f"Created JSON cache for device {device_id}, command: {command}"
            )
            return cache_entry

    @staticmethod
    def get_cache(
        db: Session, device_id: str, command: Optional[str] = None
    ) -> Optional[JSONBlobCache] | List[JSONBlobCache]:
        """
        Get cached JSON data for a device.

        Args:
            db: Database session
            device_id: Device UUID
            command: Optional specific command to retrieve. If None, returns all cache entries for device.

        Returns:
            JSONBlobCache or List[JSONBlobCache]: Single entry if command specified, list if not
        """
        query = db.query(JSONBlobCache).filter(JSONBlobCache.device_id == device_id)

        if command:
            result = query.filter(JSONBlobCache.command == command).first()
            logger.debug(
                f"Retrieved JSON cache for device {device_id}, command: {command}"
            )
            return result
        else:
            results = query.all()
            logger.debug(
                f"Retrieved {len(results)} JSON cache entries for device {device_id}"
            )
            return results

    @staticmethod
    def delete_cache(db: Session, device_id: str, command: Optional[str] = None) -> int:
        """
        Delete cached JSON data for a device.

        Args:
            db: Database session
            device_id: Device UUID
            command: Optional specific command to delete. If None, deletes all cache entries for device.

        Returns:
            int: Number of entries deleted
        """
        query = db.query(JSONBlobCache).filter(JSONBlobCache.device_id == device_id)

        if command:
            query = query.filter(JSONBlobCache.command == command)

        count = query.delete()
        db.commit()

        if command:
            logger.info(
                f"Deleted JSON cache for device {device_id}, command: {command} ({count} entries)"
            )
        else:
            logger.info(
                f"Deleted all JSON cache entries for device {device_id} ({count} entries)"
            )

        return count

    @staticmethod
    def get_all_cached_devices(db: Session) -> List[str]:
        """
        Get list of all device IDs that have cached JSON data.

        Args:
            db: Database session

        Returns:
            List[str]: List of unique device IDs
        """
        results = db.query(JSONBlobCache.device_id).distinct().all()
        device_ids = [r[0] for r in results]
        logger.debug(f"Retrieved {len(device_ids)} devices with JSON cache")
        return device_ids

    @staticmethod
    def get_cached_commands(db: Session, device_id: str) -> List[str]:
        """
        Get list of all cached commands for a device.

        Args:
            db: Database session
            device_id: Device UUID

        Returns:
            List[str]: List of commands that have cached data
        """
        results = (
            db.query(JSONBlobCache.command)
            .filter(JSONBlobCache.device_id == device_id)
            .all()
        )
        commands = [r[0] for r in results]
        logger.debug(
            f"Retrieved {len(commands)} cached commands for device {device_id}"
        )
        return commands

    @staticmethod
    def get_ttl_minutes(db: Session) -> int:
        """
        Get JSON blob cache TTL from settings.

        Args:
            db: Database session

        Returns:
            int: TTL in minutes (default: 30)
        """
        try:
            settings = (
                db.query(AppSettings)
                .filter(AppSettings.key == "cache_settings")
                .first()
            )

            if settings and settings.value:
                cache_settings = json.loads(settings.value)
                ttl = cache_settings.get("jsonBlobTtlMinutes", 30)
                logger.debug(f"Retrieved JSON blob cache TTL: {ttl} minutes")
                return ttl
        except Exception as e:
            logger.warning(f"Failed to load JSON blob cache TTL from settings: {e}")

        # Default: 30 minutes
        return 30

    @staticmethod
    def is_cache_valid(db: Session, cache_entry: JSONBlobCache) -> bool:
        """
        Check if a cache entry is still valid (not expired).

        Args:
            db: Database session
            cache_entry: The cache entry to check

        Returns:
            bool: True if cache is valid, False if expired
        """
        if not cache_entry or not cache_entry.updated_at:
            return False

        ttl_minutes = JSONCacheService.get_ttl_minutes(db)
        expiration_time = cache_entry.updated_at + timedelta(minutes=ttl_minutes)
        now = (
            datetime.now(cache_entry.updated_at.tzinfo)
            if cache_entry.updated_at.tzinfo
            else datetime.utcnow()
        )

        is_valid = now < expiration_time
        logger.debug(
            f"Cache validity check: updated_at={cache_entry.updated_at}, expiration={expiration_time}, now={now}, valid={is_valid}"
        )
        return is_valid

    @staticmethod
    def get_valid_cache(
        db: Session, device_id: str, command: str
    ) -> Optional[JSONBlobCache]:
        """
        Get cached JSON data only if it's still valid (not expired).

        Args:
            db: Database session
            device_id: Device UUID
            command: Command to retrieve cache for

        Returns:
            JSONBlobCache or None: Cache entry if valid, None if expired or not found
        """
        cache_entry = JSONCacheService.get_cache(db, device_id, command)

        if cache_entry and JSONCacheService.is_cache_valid(db, cache_entry):
            logger.info(f"Valid cache found for device {device_id}, command: {command}")
            return cache_entry
        elif cache_entry:
            logger.info(f"Cache expired for device {device_id}, command: {command}")
        else:
            logger.debug(f"No cache found for device {device_id}, command: {command}")

        return None
