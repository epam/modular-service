from service.adapter_client import AdapterClient
from service.config import ConfigurationProvider
from service.logger import get_logger

SYSTEM_LOG = get_logger('service.initializer')


def init_configuration():
    config = ConfigurationProvider()
    adapter_sdk = AdapterClient(adapter_api=config.api_link,
                                token=config.access_token)
    return adapter_sdk
