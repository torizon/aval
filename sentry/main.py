#!/usr/bin/env python3

import psycopg2
from datetime import datetime, timedelta
import os
import sys

DB_NAME = os.environ.get("POSTGRES_DB")
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
DB_HOST = os.environ.get("POSTGRES_HOST")
DB_PORT = os.environ.get("POSTGRES_PORT")

TABLE_NAME = "devices"
IS_LOCKED_COLUMN = "is_locked"
TIMESTAMP_COLUMN = "timestamp"


def check_and_update_lock():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        cur = conn.cursor()

        # Check for locked entries older than 3 hours
        three_hours_ago = datetime.now() - timedelta(hours=3)
        query = f"""
        UPDATE {TABLE_NAME}
        SET {IS_LOCKED_COLUMN} = FALSE, {TIMESTAMP_COLUMN} = NOW()
        WHERE {IS_LOCKED_COLUMN} = TRUE AND {TIMESTAMP_COLUMN} < %s
        RETURNING device_uuid
        """
        cur.execute(query, (three_hours_ago,))

        updated_rows = cur.fetchall()

        if updated_rows:
            print(f"Updated {len(updated_rows)} rows.")
        else:
            print("No rows needed updating.")

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    check_and_update_lock()
