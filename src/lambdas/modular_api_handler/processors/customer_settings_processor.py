from modular_sdk.services.customer_settings_service import \
    CustomerSettingsService
from routes.route import Route

from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SP

_LOG = get_logger(__name__)


class CustomerSettingsProcessor(AbstractCommandProcessor):
    def __init__(self, customer_settings_service: CustomerSettingsService):
        self._css = customer_settings_service

    @classmethod
    def build(cls) -> 'CustomerSettingsProcessor':
        return cls(
            customer_settings_service=SP.modular.customer_settings_service()
        )

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        return ()
