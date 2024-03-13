import json
import logging
import os
from sys import stdout
from typing import TypeVar
from commons.constants import Env

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

logger = logging.getLogger('modular-service-api')
logger.propagate = False
console_handler = logging.StreamHandler(stream=stdout)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(console_handler)

log_level = os.getenv(Env.LOG_LEVEL) or 'DEBUG'
try:
    logger.setLevel(log_level)
except ValueError:  # not valid log level name
    logger.setLevel(logging.INFO)
logging.captureWarnings(True)


def get_logger(log_name, level=log_level):
    module_logger = logger.getChild(log_name)
    if level:
        module_logger.setLevel(level)
    return module_logger


SECRET_KEYS = {
    'refresh_token', 'id_token', 'password', 'authorization', 'secret',
    'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'git_access_secret',
    'api_key', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET',
    'GOOGLE_APPLICATION_CREDENTIALS', 'private_key', 'private_key_id',
    'Authorization', 'Authentication', 'certificate'
}

JT = TypeVar('JT')  # json type


def hide_secret_values(obj: JT, secret_keys: set[str] | None = None,
                       replacement: str = '****') -> JT:
    """
    Does not change the incoming object, creates a new one. The event after
    this function is just supposed to be printed.
    :param obj:
    :param secret_keys:
    :param replacement:
    :return:
    """
    if not secret_keys:
        secret_keys = SECRET_KEYS
    match obj:
        case dict():
            res = {}
            for k, v in obj.items():
                if k in secret_keys:
                    res[k] = replacement
                else:
                    res[k] = hide_secret_values(v, secret_keys, replacement)
            return res
        case list():
            return [
                hide_secret_values(v, secret_keys, replacement) for v in obj
            ]
        case str():
            try:
                return hide_secret_values(
                    json.loads(obj),
                    secret_keys,
                    replacement
                )
            except json.JSONDecodeError:
                return obj
        case _:
            return obj
