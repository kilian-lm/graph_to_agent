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

        # Add method, class, and line number to the log formatter
        self.formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(funcName)s:%(lineno)d - %(message)s')
        self.file_handler.setFormatter(self.formatter)
        self.stream_handler.setFormatter(self.formatter)

        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.stream_handler)

    # def get_caller_info(self):
    #     stack = inspect.stack()
    #
    #     # Iterate over the stack in reverse to find the first caller outside of this logger
    #     for frame_info in reversed(stack):
    #         if frame_info.frame.f_globals['__name__'] != __name__:
    #             module = inspect.getmodule(frame_info.frame)
    #             module_name = module.__name__ if module else 'UnknownModule'
    #
    #             if 'self' in frame_info.frame.f_locals:
    #                 # Instance method call
    #                 class_name = frame_info.frame.f_locals['self'].__class__.__name__
    #                 method_name = frame_info.function
    #                 lineno = frame_info.lineno
    #                 return f'{module_name}.{class_name}.{method_name}:{lineno}'
    #             elif module_name != 'UnknownModule':
    #                 # Function call in a module
    #                 return f'{module_name}.{frame_info.function}:{frame_info.lineno}'
    #
    #     return 'UnknownCaller'

    def get_caller_info(self):
        stack = inspect.stack()

        for frame_info in stack:
            # Check if the frame is not part of the CustomLogger
            if frame_info.frame.f_globals['__name__'] != __name__:
                # Extract module, class, method, and line number
                module = inspect.getmodule(frame_info.frame)
                module_name = module.__name__ if module else 'UnknownModule'
                class_name = None
                if 'self' in frame_info.frame.f_locals:
                    class_name = frame_info.frame.f_locals['self'].__class__.__name__
                method_name = frame_info.function
                lineno = frame_info.lineno

                if class_name:
                    return f'{module_name}.{class_name}.{method_name}:{lineno}'
                else:
                    return f'{module_name}.{method_name}:{lineno}'

        return 'UnknownCaller'

    def debug(self, message):
        caller_info = self.get_caller_info()
        self.logger.debug(f'{caller_info} - {message}')

    def info(self, message):
        caller_info = self.get_caller_info()
        self.logger.info(f'{caller_info} - {message}')

    def warning(self, message):
        caller_info = self.get_caller_info()
        self.logger.warning(f'{caller_info} - {message}')

    def error(self, message):
        caller_info = self.get_caller_info()
        self.logger.error(f'{caller_info} - {message}')

    def critical(self, message):
        caller_info = self.get_caller_info()
        self.logger.critical(f'{caller_info} - {message}')

# class CustomLogger():
#     def __init__(self, log_file, log_level=logging.DEBUG, log_dir='temp_log'):
#         self.logger = logging.getLogger(self.get_caller_info())
#         self.logger.setLevel(log_level)
#
#         self.log_dir = log_dir
#         if not os.path.exists(log_dir):
#             os.makedirs(log_dir)
#
#         self.log_file = os.path.join(log_dir, log_file)
#
#         self.file_handler = logging.FileHandler(self.log_file)
#         self.file_handler.setLevel(log_level)
#
#         self.stream_handler = logging.StreamHandler()
#         self.stream_handler.setLevel(log_level)
#
#         # Add method and line number to the log formatter
#         self.formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(funcName)s:%(lineno)d - %(message)s')
#         self.file_handler.setFormatter(self.formatter)
#         self.stream_handler.setFormatter(self.formatter)
#
#         self.logger.addHandler(self.file_handler)
#         self.logger.addHandler(self.stream_handler)
#
#     def get_caller_info(self):
#         frame = inspect.stack()[2]
#         module = inspect.getmodule(frame[0])
#         class_name = None
#         method_name = None
#         if module:
#             class_name = module.__name__
#         if 'self' in frame[0].f_locals:
#             method_name = frame[0].f_code.co_name
#         return f'{class_name}.{method_name}' if class_name and method_name else class_name
#
#     def debug(self, message):
#         self.logger.debug(message)
#
#     def info(self, message):
#         self.logger.info(message)
#
#     def warning(self, message):
#         self.logger.warning(message)
#
#     def error(self, message):
#         self.logger.error(message)
#
#     def critical(self, message):
#         self.logger.critical(message)