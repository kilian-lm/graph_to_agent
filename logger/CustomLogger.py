import logging
import inspect
import os
from datetime import datetime


class CustomLogger:
    def __init__(self, log_level=logging.INFO):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(pathname)s %(class)s %(method)s:%(lineno)d - %(message)s'
        )

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(self, log_level, message):
        frame = inspect.currentframe().f_back
        directory = os.path.dirname(os.path.abspath(__file__))
        class_name = frame.f_globals['__name__']
        method_name = frame.f_code.co_name
        line_number = frame.f_lineno

        log_message = message
        extra_info = {
            'directory': directory,
            'class': class_name,
            'method': method_name,
            'line_number': line_number,
        }

        if log_level == 'DEBUG':
            self.logger.debug(log_message, extra=extra_info)
        elif log_level == 'INFO':
            self.logger.info(log_message, extra=extra_info)
        elif log_level == 'WARNING':
            self.logger.warning(log_message, extra=extra_info)
        elif log_level == 'ERROR':
            self.logger.error(log_message, extra=extra_info)
        elif log_level == 'CRITICAL':
            self.logger.critical(log_message, extra=extra_info)

    def debug(self, message):
        self.log('DEBUG', message)

    def info(self, message):
        self.log('INFO', message)

    def warning(self, message):
        self.log('WARNING', message)

    def error(self, message):
        self.log('ERROR', message)

    def critical(self, message):
        self.log('CRITICAL', message)


# if __name__ == "__main__":
#     logger = CustomLogger()
#     logger.debug("This is a debug message")
#     logger.info("This is an info message")
#     logger.warning("This is a warning message")
#     logger.error("This is an error message")
#     logger.critical("This is a critical message")
