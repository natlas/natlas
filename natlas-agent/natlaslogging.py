import logging
import time
import sys
import os
from logging.handlers import RotatingFileHandler

FORMATTER = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")
logging.Formatter.converter = time.gmtime # Always log in GMT

def setup_logging_dir():
	if not os.path.isdir("logs"):
		os.mkdir("logs")
	return True

def get_console_handler():
	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setFormatter(FORMATTER)
	return console_handler

def get_file_handler():
	file_handler = RotatingFileHandler("logs/agent.log", maxBytes=1024*1024, backupCount=5)
	file_handler.setFormatter(FORMATTER)
	return file_handler

def getLogger(name):
	setup_logging_dir()
	logger = logging.getLogger(name)
	logger.setLevel(logging.DEBUG)
	logger.addHandler(get_console_handler())
	logger.addHandler(get_file_handler())
	logger.propagate = False
	return logger