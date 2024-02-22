
from http import HTTPStatus

from routes.route import Route

from commons.constants import (
    Endpoint,
    HTTPMethod,
)
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.customer_mutator_service import CustomerMutatorService
from services.tenant_mutator_service import TenantMutatorService
from validators.request import TenantDelete, TenantGet, TenantPost
from validators.utils import validate_kwargs

_LOG = get_logger(__name__)


class TenantProcessor(AbstractCommandProcessor):
    def __init__(self, customer_service: CustomerMutatorService,
                 tenant_service: TenantMutatorService):
        self.customer_service: CustomerMutatorService = customer_service
        self.tenant_service: TenantMutatorService = tenant_service

    @classmethod
    def build(cls) -> 'TenantProcessor':
        return cls(
            customer_service=SERVICE_PROVIDER.customer_service,
            tenant_service=SERVICE_PROVIDER.tenant_service
        )

    @classmethod
    def routes(cls) -> list[Route]:
        name = cls.controller_name()
        endpoint = Endpoint.TENANTS.value
        return [
            Route(None, endpoint, controller=name, action='get',
                  conditions={'method': [HTTPMethod.GET]}),
            Route(None, endpoint, controller=name, action='post',
                  conditions={'method': [HTTPMethod.POST]}),
            Route(None, endpoint, controller=name, action='delete',
                  conditions={'method': [HTTPMethod.DELETE]}),
        ]

    @validate_kwargs
    def get(self, event: TenantGet):
        name = event.name

        if name:
            _LOG.debug(f'Describing tenant by name \'{name}\'')
            tenants = [self.tenant_service.get(tenant_name=name)]
        else:
            _LOG.debug('Describing all tenants')
            tenants = self.tenant_service.scan_tenants()

        tenants = [tenant for tenant in tenants if tenant]

        if not tenants:
            _LOG.warning('No tenants found matching given query')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'No tenants found matching given query'
            ).exc()

        _LOG.debug('Describing tenants dto')
        response = [self.tenant_service.get_dto(tenant)
                    for tenant in tenants]
        _LOG.debug(f'Response: {response}')

        return build_response(content=response)

    @validate_kwargs
    def post(self, event: TenantPost):

        name = event.name
        tenant_exist = self.tenant_service.get(tenant_name=name)
        if tenant_exist:
            _LOG.warning(f'Tenant with name \'{name}\' already exist.')
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'Tenant with name \'{name}\' already exist.'
            ).exc()

        _LOG.debug('Creating tenant')
        tenant = self.tenant_service.create(
            tenant_name=name,
            display_name=event.display_name,
            customer_name=event.tenant_customer,
            cloud=event.cloud.value,
            acc=event.acc,
            is_active=True,
            read_only=event.read_only
        )
        _LOG.debug('Saving tenant')
        self.tenant_service.save(tenant=tenant)

        _LOG.debug('Describing tenant dto')
        response = self.tenant_service.get_dto(tenant=tenant)
        _LOG.debug(f'Response: {response}')

        return build_response(content=response)

    @validate_kwargs
    def delete(self, event: TenantDelete):

        name = event.name
        _LOG.debug(f'Describing tenant by name \'{name}\'')
        tenant = self.tenant_service.get(tenant_name=name)

        if not tenant:
            _LOG.warning(f'Tenant with name \'{name}\' does not exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Tenant with name \'{name}\' does not exist.'
            ).exc()

        _LOG.debug(f'Deactivating tenant \'{name}\'')
        self.tenant_service.mark_deactivated(tenant=tenant)

        _LOG.debug('Describing tenant dto')
        response = self.tenant_service.get_dto(tenant)
        return build_response(content=response)
