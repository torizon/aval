import os
import logging


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

    logger = logging.getLogger(__name__)
    return logger
