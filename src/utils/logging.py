import logging


def get_client_logger(name: str | None = None, level: int = logging.INFO) -> logging.Logger:
    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    return logger


def get_library_logger(name: str):
    logger = logging.getLogger(name)
    logger.addHandler(logging.NullHandler())
    return logger
