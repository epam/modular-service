import getpass
import os
import traceback
from logging import (DEBUG, getLogger, Formatter, StreamHandler, INFO,
                     NullHandler)

FILE_NAME = 'modular_service_admin_cli.service.log'
LOG_FOLDER = 'logs'

user_name = getpass.getuser()

modular_service_admin_cli_logger = getLogger('modular_service_admin_cli')
modular_service_admin_cli_logger.propagate = False

debug_mode = os.getenv('MODULAR_CLI_DEBUG') == 'true'
if debug_mode:
    console_handler = StreamHandler()
    console_handler.setLevel(DEBUG)
    logFormatter = Formatter('%(asctime)s [USER: {}] %(message)s'.format(
        user_name))
    console_handler.setFormatter(logFormatter)
    modular_service_admin_cli_logger.addHandler(console_handler)
else:
    modular_service_admin_cli_logger.addHandler(NullHandler())

# define user logger to print messages
modular_cli_user_logger = getLogger('modular.user')
# console output
console_handler = StreamHandler()
console_handler.setLevel(INFO)
console_handler.setFormatter(Formatter('%(message)s'))
modular_cli_user_logger.addHandler(console_handler)


def get_logger(log_name, level=DEBUG):
    module_logger = modular_service_admin_cli_logger.getChild(log_name)
    if level:
        module_logger.setLevel(level)
    return module_logger


def get_user_logger(log_name, level=INFO):
    module_logger = modular_cli_user_logger.getChild(log_name)
    if level:
        module_logger.setLevel(level)
    return module_logger


def exception_handler_formatter(exception_type, exception, exc_traceback):
    if debug_mode:
        modular_service_admin_cli_logger.error('%s: %s', exception_type.__name__, exception)
        traceback.print_tb(tb=exc_traceback, limit=15)
