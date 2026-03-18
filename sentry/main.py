#!/usr/bin/env python3

import psycopg2
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aws_database.ssm_tunnel import close_ssm_tunnel, ensure_ssm_tunnel  # noqa: E402

if os.environ.get("AWS_RDS_HOST"):
    from aws_database.generate_token import generate_token

DB_NAME = os.environ.get("POSTGRES_DB")
DB_USER = os.environ.get("POSTGRES_USER")

TABLE_NAME = "devices"
IS_LOCKED_COLUMN = "is_locked"
TIMESTAMP_COLUMN = "timestamp"


def get_connection_settings():
    if os.environ.get("AWS_RDS_HOST"):
        print("AWS_RDS_HOST detected -> using SSM tunnel + IAM authentication")
        ensure_ssm_tunnel()
        print("Using IAM token for database authentication (host=localhost)")
        return generate_token(), "localhost", os.environ["LOCAL_PORT"]

    print("AWS_RDS_HOST not set -> using direct database connection")
    return (
        os.environ.get("POSTGRES_PASSWORD"),
        os.environ.get("POSTGRES_HOST"),
        os.environ.get("POSTGRES_PORT"),
    )


def check_and_update_lock():
    try:
        db_password, db_host, db_port = get_connection_settings()
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        cur = conn.cursor()

        # Check for locked entries older than 3 minutes
        three_minutes_ago = datetime.now() - timedelta(minutes=3)
        query = f"""
        UPDATE {TABLE_NAME}
        SET {IS_LOCKED_COLUMN} = FALSE, {TIMESTAMP_COLUMN} = NOW()
        WHERE {IS_LOCKED_COLUMN} = TRUE AND {TIMESTAMP_COLUMN} < %s
        RETURNING device_uuid
        """
        cur.execute(query, (three_minutes_ago,))

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
    try:
        check_and_update_lock()
    finally:
        close_ssm_tunnel()
