import logging
import time
import sys
from logging.handlers import RotatingFileHandler

FORMATTER = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")
logging.Formatter.converter = time.gmtime # Always log in GMT

def get_console_handler():
	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setFormatter(FORMATTER)
	return console_handler

def get_file_handler():
	file_handler = RotatingFileHandler("logs/agent.log", maxBytes=1024*1024, backupCount=5)
	file_handler.setFormatter(FORMATTER)
	return file_handler

def getLogger(name):
	logger = logging.getLogger(name)
	logger.setLevel(logging.DEBUG)
	logger.addHandler(get_console_handler())
	logger.addHandler(get_file_handler())
	logger.propagate = False
	return logger