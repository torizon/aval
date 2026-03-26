import os
import sys
from pathlib import Path
import boto3

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging_setup  # noqa: E402

logger = logging_setup.setup_logging()


def generate_token():
    region = os.environ["AWS_DEFAULT_REGION"]
    host = os.environ["AWS_RDS_HOST"]
    user = os.environ["POSTGRES_USER"]
    port = int(os.environ["REMOTE_PORT"])

    logger.debug(
        "Generating AWS RDS IAM auth token for host=%s port=%s user=%s region=%s",
        host,
        port,
        user,
        region,
    )

    client = boto3.client(
        "rds",
        region_name=region,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )

    token = client.generate_db_auth_token(
        DBHostname=host,
        Port=port,
        DBUsername=user,
    )

    logger.info("AWS RDS IAM auth token generated successfully")
    return token


if __name__ == "__main__":
    logger.info("generate_token.py executed successfully: %s", generate_token())
