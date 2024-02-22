
from http import HTTPStatus

from routes.route import Route

from commons import validate_params
from commons.constants import Endpoint, HTTPMethod, REGION_ATTR, TENANT_ATTR
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.region_mutator_service import RegionMutatorService
from services.tenant_mutator_service import TenantMutatorService

_LOG = get_logger(__name__)


class TenantRegionProcessor(AbstractCommandProcessor):
    def __init__(self, tenant_service: TenantMutatorService,
                 region_service: RegionMutatorService):
        self.tenant_service = tenant_service
        self.region_service = region_service

    @classmethod
    def build(cls) -> 'TenantRegionProcessor':
        return cls(
            tenant_service=SERVICE_PROVIDER.tenant_service,
            region_service=SERVICE_PROVIDER.region_service
        )

    @classmethod
    def routes(cls) -> list[Route]:
        name = cls.controller_name()
        endpoint = Endpoint.TENANTS_REGIONS.value
        return [
            Route(None, endpoint, controller=name, action='get',
                  conditions={'method': [HTTPMethod.DELETE]}),
            Route(None, endpoint, controller=name, action='post',
                  conditions={'method': [HTTPMethod.DELETE]}),
            Route(None, endpoint, controller=name, action='delete',
                  conditions={'method': [HTTPMethod.DELETE]}),
        ]

    def get(self, event):
        _LOG.debug('Describe tenant regions')
        validate_params(event, (TENANT_ATTR,))

        tenant_name = event.get(TENANT_ATTR)

        _LOG.debug(f'Describing tenant by name \'{tenant_name}\'')
        tenant = self.tenant_service.get(tenant_name=tenant_name)
        if not tenant:
            _LOG.debug(f'Tenant \'{tenant_name}\' does not exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Tenant \'{tenant_name}\' does not exist.'
            ).exc()
        if not tenant.regions:
            _LOG.warning(f'Tenant \'{tenant_name}\' does not have any regions')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Tenant \'{tenant_name}\' does not have any regions'
            ).exc()
        _LOG.debug('Describing region dto.')
        response = [self.region_service.get_dto(region=region) for region
                    in tenant.regions]
        _LOG.debug(f'Response: {response}')
        return build_response(content=response)

    def post(self, event):
        _LOG.debug(f'Activate region in tenant event: {event}')

        validate_params(event, (TENANT_ATTR, REGION_ATTR))

        tenant_name = event.get(TENANT_ATTR)
        tenant = self.tenant_service.get(tenant_name=tenant_name)
        if not tenant:
            _LOG.debug(f'Tenant \'{tenant_name}\' does not exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Tenant \'{tenant_name}\' does not exist.'
            ).exc()

        region_name = event.get(REGION_ATTR)
        region = self.region_service.get_region(region_name=region_name)
        if not region:
            _LOG.debug(f'Region \'{region_name}\' is not supported.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Region \'{region_name}\'  is not supported.'
            ).exc()

        _LOG.debug(f'Activating region \'{region_name}\' in tenant '
                   f'\'{tenant_name}\'')
        self.region_service.activate_region_in_tenant(tenant=tenant,
                                                      region=region)

        _LOG.debug('Saving tenant')
        self.tenant_service.save(tenant=tenant)

        _LOG.debug('Describing region dto.')
        response = [self.region_service.get_dto(region=region) for region
                    in tenant.regions]
        _LOG.debug(f'Response: {response}')
        return build_response(content=response)

    def delete(self, event):
        _LOG.debug('Deactivate region in tenant')
        validate_params(event, (TENANT_ATTR, REGION_ATTR,))

        tenant_name = event.get(TENANT_ATTR)

        _LOG.debug(f'Describing tenant by name \'{tenant_name}\'')
        tenant = self.tenant_service.get(tenant_name=tenant_name)
        if not tenant:
            _LOG.debug(f'Tenant \'{tenant_name}\' does not exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Tenant \'{tenant_name}\' does not exist.'
            ).exc()
        region_name = event.get(REGION_ATTR)
        region = self.region_service.get_region(region_name=region_name)
        if not region:
            _LOG.debug(f'Region \'{region_name}\' is not supported.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Region \'{region_name}\'  is not supported.'
            ).exc()

        _LOG.debug(f'Deactivating region \'{region_name}\' from tenant '
                   f'\'{tenant_name}\'')
        self.region_service.delete_region_from_tenant(
            tenant=tenant,
            region=region
        )

        _LOG.debug('Saving tenant')
        self.tenant_service.save(tenant=tenant)

        _LOG.debug('Extracting region dto')
        response = self.tenant_service.get_dto(tenant=tenant)
        _LOG.debug(f'Response: {response}')

        return build_response(content=response)
