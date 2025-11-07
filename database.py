import os
import time
import psycopg
import logging
from contextlib import contextmanager
import threading

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


_heartbeat_thread = None
_heartbeat_stop_event = None


# Update the timestamp every 2 minutes
def _heartbeat_worker(device_uuid, stop_event, interval=120):
    logger.info(f"Heartbeat thread started for {device_uuid}")
    while not stop_event.is_set():
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE devices SET timestamp = NOW() WHERE device_uuid = %s",
                        (device_uuid,),
                    )
                    conn.commit()
            logger.debug(f"Heartbeat updated for {device_uuid}")
        except Exception as e:
            logger.error(f"Error updating heartbeat for {device_uuid}: {e}")

        # Waits for the interval, but exits sooner if stop_event is set
        stop_event.wait(interval)

    logger.info(f"Heartbeat thread stopped for {device_uuid}")


def acquire_lock(device_uuid):
    global _heartbeat_thread, _heartbeat_stop_event

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

                _heartbeat_stop_event = threading.Event()
                _heartbeat_thread = threading.Thread(
                    target=_heartbeat_worker,
                    args=(device_uuid, _heartbeat_stop_event),
                    daemon=True,
                )
                _heartbeat_thread.start()

                return True
            logger.info(
                f"Failed to acquire lock for device {device_uuid}. Device is already locked or doesn't exist."
            )
            return False


def release_lock(device_uuid):
    global _heartbeat_thread, _heartbeat_stop_event

    logger.info(f"Attempting to release lock for device {device_uuid}")
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE devices SET is_locked = FALSE WHERE device_uuid = %s",
                (device_uuid,),
            )
            conn.commit()
            logger.info(f"Lock released for device {device_uuid}")

    if _heartbeat_thread and _heartbeat_stop_event:
        _heartbeat_stop_event.set()
        _heartbeat_thread.join(timeout=5)
        logger.info(f"Heartbeat thread stopped for {device_uuid}")
        _heartbeat_thread = None
        _heartbeat_stop_event = None


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
