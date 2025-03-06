from commons.log_helper import get_logger
from http import HTTPStatus
from modular_sdk.commons import ModularException
from modular_sdk.commons.constants import ALL_PARENT_TYPES
from modular_sdk.models.parent import Parent
from modular_sdk.services.application_service import ApplicationService
from modular_sdk.services.customer_service import CustomerService
from modular_sdk.services.parent_service import ParentService
from modular_sdk.services.tenant_service import TenantService

_LOG = get_logger(__name__)


class ParentMutatorService(ParentService):

    def __init__(self, application_service: ApplicationService,
                 tenant_service: TenantService,
                 customer_service: CustomerService):
        super().__init__(tenant_service=tenant_service,
                         customer_service=customer_service)
        self.application_service = application_service

    def update(self, parent: Parent, application_id=None, parent_type=None,
               description=None):
        if application_id:
            _LOG.debug(f'Updating parent application_id to '
                       f'\'{application_id}\'')
            application = self.application_service.get_application_by_id(
                application_id=application_id
            )
            if not application:
                _LOG.error(f'Application with specified id '
                           f'\'{application_id}\' does not exist.')
                raise ModularException(
                    code=HTTPStatus.NOT_FOUND.value,
                    content=f'Application with specified id '
                            f'\'{application_id}\' does not exist.'
                )
            parent.application_id = application_id
        if parent_type:
            _LOG.debug(f'Updating parent type to \'{parent_type}\'')
            if parent_type not in ALL_PARENT_TYPES:
                _LOG.error(f'Invalid parent type specified \'{parent_type}\'. '
                           f'Available options: {ALL_PARENT_TYPES}')
                raise ModularException(
                    code=HTTPStatus.BAD_REQUEST,
                    content=f'Invalid parent type specified \'{parent_type}\'. '
                            f'Available options: {ALL_PARENT_TYPES}'
                )
            parent.type = parent_type
        if description:
            _LOG.debug(f'Updating parent description to \'{description}\'')
            parent.description = description
