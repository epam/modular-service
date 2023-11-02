import os
from pathlib import Path

from modular_service_admin_cli.service.adapter_client import AdapterClient
from modular_service_admin_cli.service.config import ConfigurationProvider
from modular_service_admin_cli.service.logger import get_logger

SYSTEM_LOG = get_logger('modular_service_admin_cli.service.initializer')


def init_configuration():
    config = ConfigurationProvider()
    adapter_sdk = AdapterClient(adapter_api=config.api_link,
                                token=config.access_token)
    return adapter_sdk
