from typing import List

from routes.route import Route

from commons import RESPONSE_BAD_REQUEST_CODE, validate_params, build_response, \
    RESPONSE_RESOURCE_NOT_FOUND_CODE, \
    RESPONSE_OK_CODE
from commons.constants import GET_METHOD, POST_METHOD, DELETE_METHOD, \
    NAME_ATTR, CLOUD_ATTR, TENANT_CUSTOMER_ATTR, \
    DISPLAY_NAME_ATTR, READ_ONLY_ATTR
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import \
    AbstractCommandProcessor
from services import SERVICE_PROVIDER
from services.customer_mutator_service import CustomerMutatorService
from services.tenant_mutator_service import TenantMutatorService

_LOG = get_logger(__name__)


class TenantProcessor(AbstractCommandProcessor):
    def __init__(self, customer_service: CustomerMutatorService,
                 tenant_service: TenantMutatorService):
        self.customer_service: CustomerMutatorService = customer_service
        self.tenant_service: TenantMutatorService = tenant_service

    @classmethod
    def build(cls) -> 'TenantProcessor':
        return cls(
            customer_service=SERVICE_PROVIDER.customer_service(),
            tenant_service=SERVICE_PROVIDER.tenant_service()
        )

    @classmethod
    def routes(cls) -> List[Route]:
        name = cls.controller_name()
        return [
            Route(None, '/tenants', controller=name, action='get',
                  conditions={'method': [GET_METHOD]}),
            Route(None, '/tenants', controller=name, action='post',
                  conditions={'method': [POST_METHOD]}),
            Route(None, '/tenants', controller=name, action='delete',
                  conditions={'method': [DELETE_METHOD]}),
        ]

    def get(self, event):
        _LOG.debug(f'Describe tenant event: {event}')

        name = event.get(NAME_ATTR)

        if name:
            _LOG.debug(f'Describing tenant by name \'{name}\'')
            tenants = [self.tenant_service.get(tenant_name=name)]
        else:
            _LOG.debug(f'Describing all tenants')
            tenants = self.tenant_service.scan_tenants()

        tenants = [tenant for tenant in tenants if tenant]

        if not tenants:
            _LOG.error(f'No tenants found matching given query')
            return build_response(
                code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                content=f'No tenants found matching given query'
            )

        _LOG.debug(f'Describing tenants dto')
        response = [self.tenant_service.get_dto(tenant)
                    for tenant in tenants]
        _LOG.debug(f'Response: {response}')

        return build_response(
            code=RESPONSE_OK_CODE,
            content=response
        )

    def post(self, event):
        _LOG.debug(f'Activate tenant event: {event}')
        validate_params(event, (NAME_ATTR, DISPLAY_NAME_ATTR,
                                TENANT_CUSTOMER_ATTR, CLOUD_ATTR))

        name = event.get(NAME_ATTR)
        tenant_exist = self.tenant_service.get(tenant_name=name)
        if tenant_exist:
            _LOG.error(f'Tenant with name \'{name}\' already exist.')
            return build_response(
                code=RESPONSE_BAD_REQUEST_CODE,
                content=f'Tenant with name \'{name}\' already exist.'
            )

        tenant_customer = event.get(TENANT_CUSTOMER_ATTR)
        cloud = event.get(CLOUD_ATTR)
        acc = event.get('acc')
        display_name = event.get(DISPLAY_NAME_ATTR)

        read_only = event.get(READ_ONLY_ATTR, 'f')
        if not isinstance(read_only, bool):
            read_only = True if read_only.lower() in ('y', 'true') else False

        _LOG.debug(f'Creating tenant')
        tenant = self.tenant_service.create(
            tenant_name=name,
            display_name=display_name,
            customer_name=tenant_customer,
            cloud=cloud,
            acc=acc,
            is_active=True,
            read_only=read_only
        )
        _LOG.debug(f'Saving tenant')
        self.tenant_service.save(tenant=tenant)

        _LOG.debug(f'Describing tenant dto')
        response = self.tenant_service.get_dto(tenant=tenant)
        _LOG.debug(f'Response: {response}')

        return build_response(
            code=RESPONSE_OK_CODE,
            content=response
        )

    def delete(self, event):
        _LOG.debug(f'Deactivate tenant event: {event}')
        validate_params(event, (NAME_ATTR,))

        name = event.get(NAME_ATTR)
        _LOG.debug(f'Describing tenant by name \'{name}\'')
        tenant = self.tenant_service.get(tenant_name=name)

        if not tenant:
            _LOG.error(f'Tenant with name \'{name}\' does not exist.')
            return build_response(
                code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                content=f'Tenant with name \'{name}\' does not exist.'
            )

        _LOG.debug(f'Deactivating tenant \'{name}\'')
        self.tenant_service.mark_deactivated(tenant=tenant)

        _LOG.debug(f'Describing tenant dto')
        response = self.tenant_service.get_dto(tenant)
        _LOG.debug(f'Response')
        return build_response(
            code=RESPONSE_OK_CODE,
            content=response
        )
