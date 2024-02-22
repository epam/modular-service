from commons.log_helper import get_logger
from modular_sdk.commons import ModularException, \
    RESPONSE_BAD_REQUEST_CODE, RESPONSE_RESOURCE_NOT_FOUND_CODE
from modular_sdk.commons.constants import AVAILABLE_APPLICATION_TYPES
from modular_sdk.models.application import Application
from modular_sdk.services.application_service import ApplicationService
from modular_sdk.services.customer_service import CustomerService

_LOG = get_logger(__name__)


class ApplicationMutatorService(ApplicationService):

    def __init__(self, customer_service: CustomerService):
        super().__init__(customer_service=customer_service)

    def update(self, application: Application, application_type=None,
               customer_id=None, description=None):
        if application_type:
            _LOG.debug(f'Updating application type to \'{application_type}\'')
            if application_type not in AVAILABLE_APPLICATION_TYPES:
                _LOG.error(f'Invalid application type specified. Available '
                           f'options: \'{AVAILABLE_APPLICATION_TYPES}\'')
                raise ModularException(
                    code=RESPONSE_BAD_REQUEST_CODE,
                    content=f'Invalid application type specified. Available '
                            f'options: \'{AVAILABLE_APPLICATION_TYPES}\''
                )
            application.type = application_type
        if customer_id:
            _LOG.debug(f'Updating application customer to \'{customer_id}\'')
            if not self.customer_service.get(name=customer_id):
                _LOG.error(
                    f'Customer with name \'{customer_id}\' does not exist.')
                raise ModularException(
                    code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                    content=f'Customer with name \'{customer_id}\' '
                            f'does not exist.'
                )
            application.customer_id = customer_id
        if description:
            _LOG.debug(f'Updating application description '
                       f'to \'{description}\'')
            application.description = description