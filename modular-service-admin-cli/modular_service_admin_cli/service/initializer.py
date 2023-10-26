import os
from pathlib import Path

from modular_service_admin_cli.service.adapter_client import AdapterClient
from modular_service_admin_cli.service.config import ConfigurationProvider
from modular_service_admin_cli.service.logger import get_logger

SYSTEM_LOG = get_logger('modular_service_admin_cli.service.initializer')

CONFIG = None
ADAPTER_SDK = None
INITIALIZED = False


def init_configuration():
    config_path = f'{str(Path.home())}/.modular_service_admin_cli/credentials'
    if os.path.exists(config_path):
        global CONFIG, ADAPTER_SDK, INITIALIZED
        CONFIG = ConfigurationProvider()
        ADAPTER_SDK = AdapterClient(adapter_api=CONFIG.api_link,
                                    token=CONFIG.access_token)
        INITIALIZED = True
    else:
        SYSTEM_LOG.info(f'Configuration is missing by path {config_path}. '
                        f'Initialization skipped.')


if not INITIALIZED:
    init_configuration()
