import os
import psycopg2
from contextlib import contextmanager

DB_PARAMS = {
    "dbname": os.environ["POSTGRES_DB"],
    "user": os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
    "host": os.environ["POSTGRES_HOST"],
    "port": os.environ["POSTGRES_PORT"],
}


@contextmanager
def get_db_connection():
    conn = psycopg2.connect(**DB_PARAMS)
    try:
        yield conn
    finally:
        conn.close()


def acquire_lock(device_uuid):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT is_locked FROM devices WHERE device_uuid = %s FOR UPDATE",
                (device_uuid,),
            )
            result = cursor.fetchone()
            if result and not result[0]:
                cursor.execute(
                    "UPDATE devices SET is_locked = TRUE WHERE device_uuid = %s",
                    (device_uuid,),
                )
                conn.commit()
                return True
            return False


def release_lock(device_uuid):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE devices SET is_locked = FALSE WHERE device_uuid = %s",
                (device_uuid,),
            )
            conn.commit()


def device_exists(device_uuid):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM devices WHERE device_uuid = %s", (device_uuid,)
            )
            return cursor.fetchone() is not None


def create_device(device_uuid):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO devices (device_uuid, is_locked) VALUES (%s, FALSE)",
                (device_uuid,),
            )
            conn.commit()
