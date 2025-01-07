import os
import time
import psycopg
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_PARAMS = {
    "dbname": os.environ["POSTGRES_DB"],
    "user": os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
    "host": os.environ["POSTGRES_HOST"],
    "port": os.environ["POSTGRES_PORT"],
}


@contextmanager
def get_db_connection():
    conn = psycopg.connect(**DB_PARAMS)
    try:
        yield conn
    finally:
        conn.close()


def acquire_lock(device_uuid):
    logger.info(f"Attempting to acquire lock for device {device_uuid}")
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT is_locked FROM devices WHERE device_uuid = %s FOR UPDATE",
                (device_uuid,),
            )
            result = cursor.fetchone()
            if result and not result[0]:
                cursor.execute(
                    "UPDATE devices SET is_locked = TRUE, timestamp = NOW() WHERE device_uuid = %s",
                    (device_uuid,),
                )
                conn.commit()
                logger.info(
                    f"Lock acquired successfully for device {device_uuid}"
                )
                return True
            logger.info(
                f"Failed to acquire lock for device {device_uuid}. Device is already locked or doesn't exist."
            )
            return False


def release_lock(device_uuid):
    logger.info(f"Attempting to release lock for device {device_uuid}")
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE devices SET is_locked = FALSE WHERE device_uuid = %s",
                (device_uuid,),
            )
            conn.commit()
            logger.info(f"Lock released for device {device_uuid}")


def device_exists(device_uuid):
    logger.info(f"Checking if device {device_uuid} exists")
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM devices WHERE device_uuid = %s", (device_uuid,)
            )
            exists = cursor.fetchone() is not None
            logger.info(
                f"Device {device_uuid} {'exists' if exists else 'does not exist'}"
            )
            return exists


def create_device(device_uuid):
    logger.info(f"Attempting to create device {device_uuid}")
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO devices (device_uuid, is_locked) VALUES (%s, FALSE)",
                (device_uuid,),
            )
            conn.commit()
            logger.info(f"Device {device_uuid} created successfully")


def try_until_locked(device_uuid, max_attempts=80, sleep=90, fail_fast=True):
    if fail_fast:
        return acquire_lock(device_uuid)

    attempts = 0
    while attempts < max_attempts:
        if acquire_lock(device_uuid):
            logger.info(f"Device {device_uuid} successfully locked.")
            return True
        else:
            logger.info(
                f"Device {device_uuid} is already locked. Retrying in {sleep} seconds..."
            )
            time.sleep(sleep)
            attempts += 1

    raise Exception(
        f"Wasn't able to lock the device {device_uuid} after {max_attempts} attempts. :("
    )
