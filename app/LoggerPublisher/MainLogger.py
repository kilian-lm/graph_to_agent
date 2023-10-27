import logging
import os
import boto3
from dotenv import load_dotenv

load_dotenv()


class MainLogger():
    def __init__(self, param_bucket_name, log_file, log_level=logging.DEBUG, log_dir='temp_log'):

        self.param_bucket_name = param_bucket_name
        self.ACCESS_KEY = os.environ.get('ACCESS_KEY')
        self.SECRET_KEY = os.environ.get('SECRET_KEY')
        self.REGION = os.environ.get('REGION')

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.log_file = os.path.join(log_dir, log_file)

        self.file_handler = logging.FileHandler(self.log_file)
        self.file_handler.setLevel(log_level)

        self.stream_handler = logging.StreamHandler()
        self.stream_handler.setLevel(log_level)

        self.formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')
        self.file_handler.setFormatter(self.formatter)
        self.stream_handler.setFormatter(self.formatter)

        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.stream_handler)

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

    def save_logging(self):
        s3 = boto3.client('s3', aws_access_key_id=self.ACCESS_KEY, aws_secret_access_key=self.SECRET_KEY,
                          region_name=self.REGION)

        key = f'logs/{os.path.basename(self.log_file)}'
        s3.upload_file(self.log_file, self.param_bucket_name, key)
        self.info(f'Log file uploaded to S3 bucket: {self.param_bucket_name}/{key}')
