from datetime import date
from getpass import getuser
from logging import DEBUG, FileHandler, Formatter, NullHandler, StreamHandler, getLogger
import os
from pathlib import Path
import re

from modular_service_cli.version import __version__

LOGS_FOLDER = Path('logs/modular-service')
LOGS_FILE_NAME = date.today().strftime('%Y-%m-%d-c7n.log')

SYSTEM_LOG_FORMAT = f'%(asctime)s [USER: {getuser()}] %(message)s'
VERBOSE_MODE_LOG_FORMAT = f'%(asctime)s [%(levelname)s] ' \
                          f'USER:{getuser()} LOG: %(message)s'


class SensitiveFormatter(Formatter):
    """
    Formatter that removes sensitive information.
    """
    _inner = '|'.join((
        'refresh_token', 'id_token', 'password', 'authorization', 'secret',
        'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'git_access_secret',
        'api_key', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET',
        'GOOGLE_APPLICATION_CREDENTIALS', 'private_key', 'private_key_id',
        'Authorization', 'Authentication', 'sdk_secret_key', 'key_id',
        'certificate', 'access_token', 'refresh_token'
    ))
    # assuming that only raw python dicts will be written. This regex won't
    # catch exposed secured params inside JSON strings. In looks only for
    # single quotes
    regex = re.compile(rf"'({_inner})':\s*?'(.*?)'")

    def format(self, record):
        return re.sub(
            self.regex,
            r"'\1': '****'",
            super().format(record)
        )


logger = getLogger('modular-service')
logger.setLevel(DEBUG)
logger.propagate = False

if log_level := os.getenv('MODULAR_SERVICE_CLI_LOG_LEVEL'):
    console_handler = StreamHandler()
    try:
        console_handler.setLevel(log_level)
    except ValueError:
        console_handler.setLevel(DEBUG)
    console_handler.setFormatter(SensitiveFormatter(SYSTEM_LOG_FORMAT))
    logger.addHandler(console_handler)
else:
    logger.addHandler(NullHandler())


def get_logger(log_name: str, level=DEBUG):
    module_logger = logger.getChild(log_name)
    module_logger.setLevel(level)
    return module_logger


def write_verbose_logs():
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    file_handler = FileHandler(LOGS_FOLDER / LOGS_FILE_NAME)
    file_handler.setLevel(DEBUG)
    formatter = SensitiveFormatter(VERBOSE_MODE_LOG_FORMAT)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.info(f'modular cli version: {__version__}')
