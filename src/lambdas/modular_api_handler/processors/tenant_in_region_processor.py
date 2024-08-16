from http import HTTPStatus

from modular_sdk.models.tenant import Tenant
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
from validators.request import TenantRegionDelete, BaseModel, TenantRegionPost
from validators.response import RegionsResponse
from validators.utils import validate_kwargs

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
                Endpoint.TENANTS_NAME_REGIONS,
                HTTPMethod.GET,
                'get',
                response=(HTTPStatus.OK, RegionsResponse, None),
                permission=Permission.TENANT_DESCRIBE_REGION
            ),
            cls.route(
                Endpoint.TENANTS_NAME_REGIONS,
                HTTPMethod.POST,
                'post',
                response=(HTTPStatus.CREATED, RegionsResponse, None),
                permission=Permission.TENANT_CREATE_REGION
            ),
            cls.route(
                Endpoint.TENANTS_NAME_REGIONS,
                HTTPMethod.DELETE,
                'delete',
                response=(HTTPStatus.NO_CONTENT, None, None),
                permission=Permission.TENANT_DELETE_REGION
            )
        )

    def _get_tenant(self, name: str, customer_id: str) -> Tenant | None:
        item = self.tenant_service.get(name)
        if not item:
            item = next(self.tenant_service.i_get_by_acc(
                acc=name, limit=1
            ), None)
        if not item or item.customer_name != customer_id:
            return
        return item

    @validate_kwargs
    def get(self, event: BaseModel, name: str):
        name = name.upper()

        _LOG.debug(f'Describing tenant by name \'{name}\'')
        tenant = self._get_tenant(name, event.customer_id)
        if not tenant:
            _LOG.debug(f'Tenant \'{name}\' does not exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Tenant \'{name}\' does not exist.'
            ).exc()

        return build_response([
            self.region_service.get_dto(region) for region in tenant.regions
        ])

    @validate_kwargs
    def post(self, event: TenantRegionPost, name: str):
        name = name.upper()

        tenant = self._get_tenant(name, event.customer_id)
        if not tenant:
            _LOG.debug(f'Tenant \'{name}\' does not exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Tenant \'{name}\' does not exist.'
            ).exc()

        region_name = event.region
        region = self.region_service.get_region(region_name=region_name)
        if not region:
            _LOG.debug(f'Region \'{region_name}\' is not supported.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Region \'{region_name}\'  is not supported.'
            ).exc()

        _LOG.debug(f'Activating region \'{region_name}\' in tenant '
                   f'\'{name}\'')
        self.region_service.activate_region_in_tenant(tenant=tenant,
                                                      region=region)

        _LOG.debug('Saving tenant')
        self.tenant_service.save(tenant=tenant)

        return build_response([
            self.region_service.get_dto(region) for region in tenant.regions
        ], code=HTTPStatus.CREATED)

    @validate_kwargs
    def delete(self, event: TenantRegionDelete, name: str):
        name = name.upper()

        _LOG.debug(f'Describing tenant by name \'{name}\'')
        tenant = self._get_tenant(name, event.customer_id)
        if not tenant:
            _LOG.debug(f'Tenant \'{name}\' does not exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Tenant \'{name}\' does not exist.'
            ).exc()
        region_name = event.region
        region = self.region_service.get_region(region_name=region_name)
        if not region:
            _LOG.debug(f'Region \'{region_name}\' is not supported.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Region \'{region_name}\'  is not supported.'
            ).exc()

        _LOG.debug(f'Deactivating region \'{region_name}\' from tenant '
                   f'\'{name}\'')
        self.region_service.delete_region_from_tenant(
            tenant=tenant,
            region=region
        )

        _LOG.debug('Saving tenant')
        self.tenant_service.save(tenant=tenant)
        return build_response(code=HTTPStatus.NO_CONTENT)
