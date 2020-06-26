import logging
import time
import sys
import os
from logging.handlers import RotatingFileHandler
from config import Config
from pathlib import Path

FORMATTER = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")
logging.Formatter.converter = time.gmtime  # Always log in GMT
conf = Config()


def setup_logging_dir():
    log_dir = os.path.join(conf.data_dir, "logs")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    return log_dir


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler(log_dir):
    log_file = os.path.join(log_dir, "agent.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(name):
    log_dir = setup_logging_dir()
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler(log_dir))
    logger.propagate = False
    return logger
