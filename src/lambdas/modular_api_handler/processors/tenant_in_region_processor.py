from http import HTTPStatus

from routes.route import Route

from commons.constants import Endpoint, HTTPMethod, Permission
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.region_mutator_service import RegionMutatorService
from services.tenant_mutator_service import TenantMutatorService
from validators.request import TenantRegionDelete, TenantRegionGet, TenantRegionPost
from validators.utils import validate_kwargs
from validators.response import TenantsResponse, RegionsResponse

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
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.TENANTS_REGIONS,
                HTTPMethod.GET,
                'get',
                response=(HTTPStatus.OK, RegionsResponse, None),
                permission=Permission.REGION_DESCRIBE
            ),
            cls.route(
                Endpoint.TENANTS_REGIONS,
                HTTPMethod.POST,
                'post',
                response=(HTTPStatus.OK, RegionsResponse, None),
                permission=Permission.REGION_CREATE
            ),
            cls.route(
                Endpoint.TENANTS_REGIONS,
                HTTPMethod.DELETE,
                'delete',
                response=(HTTPStatus.OK, TenantsResponse, None),
                permission=Permission.REGION_DELETE
            )
        )

    @validate_kwargs
    def get(self, event: TenantRegionGet):

        tenant_name = event.tenant

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

    @validate_kwargs
    def post(self, event: TenantRegionPost):

        tenant_name = event.tenant
        tenant = self.tenant_service.get(tenant_name=tenant_name)
        if not tenant:
            _LOG.debug(f'Tenant \'{tenant_name}\' does not exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Tenant \'{tenant_name}\' does not exist.'
            ).exc()

        region_name = event.region
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

    @validate_kwargs
    def delete(self, event: TenantRegionDelete):

        tenant_name = event.tenant

        _LOG.debug(f'Describing tenant by name \'{tenant_name}\'')
        tenant = self.tenant_service.get(tenant_name=tenant_name)
        if not tenant:
            _LOG.debug(f'Tenant \'{tenant_name}\' does not exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Tenant \'{tenant_name}\' does not exist.'
            ).exc()
        region_name = event.region
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
