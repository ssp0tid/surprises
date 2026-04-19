import logging
import sys


def setup_logging(verbose: int = 0) -> None:
    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
