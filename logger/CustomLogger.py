import logging
import os
# import boto3
from dotenv import load_dotenv

load_dotenv()

import logging
import os
import inspect


class CustomLogger():
    def __init__(self, log_file, log_level=logging.DEBUG, log_dir='temp_log'):
        self.logger = logging.getLogger(self.get_caller_info())
        self.logger.setLevel(log_level)

        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.log_file = os.path.join(log_dir, log_file)

        self.file_handler = logging.FileHandler(self.log_file)
        self.file_handler.setLevel(log_level)

        self.stream_handler = logging.StreamHandler()
        self.stream_handler.setLevel(log_level)

        # Add method and line number to the log formatter
        self.formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(funcName)s:%(lineno)d - %(message)s')
        self.file_handler.setFormatter(self.formatter)
        self.stream_handler.setFormatter(self.formatter)

        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.stream_handler)

    def get_caller_info(self):
        frame = inspect.stack()[2]
        module = inspect.getmodule(frame[0])
        class_name = None
        method_name = None
        if module:
            class_name = module.__name__
        if 'self' in frame[0].f_locals:
            method_name = frame[0].f_code.co_name
        return f'{class_name}.{method_name}' if class_name and method_name else class_name

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)
