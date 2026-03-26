import os
import logging


def _configure_external_loggers():
    # Keep Aval verbose without flooding the output with SSH transport internals.
    for logger_name in (
        "paramiko",
        "fabric",
        "invoke",
        "botocore",
        "boto3",
        "urllib3",
    ):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def setup_logging():
    if os.getenv("AVAL_VERBOSE"):
        logging_level = logging.DEBUG

        logging.basicConfig(
            level=logging_level,
            format="%(levelname)s - %(asctime)s - File: %(filename)s, Line: %(lineno)d -  %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        logging_level = logging.INFO
        logging.basicConfig(
            level=logging_level,
            format="%(levelname)s - %(message)s",
        )

    _configure_external_loggers()
    logger = logging.getLogger(__name__)
    return logger
