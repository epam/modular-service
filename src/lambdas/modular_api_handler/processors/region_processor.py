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
from validators.request import BaseModel, RegionPost
from validators.response import RegionResponse, RegionsResponse
from validators.utils import validate_kwargs

_LOG = get_logger(__name__)


class RegionProcessor(AbstractCommandProcessor):
    def __init__(self, tenant_service: TenantMutatorService,
                 region_service: RegionMutatorService):
        self.tenant_service: TenantMutatorService = tenant_service
        self.region_service: RegionMutatorService = region_service

    @classmethod
    def build(cls) -> 'RegionProcessor':
        return cls(
            tenant_service=SERVICE_PROVIDER.tenant_service,
            region_service=SERVICE_PROVIDER.region_service,
        )

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.REGIONS,
                HTTPMethod.GET,
                'query',
                response=(HTTPStatus.OK, RegionsResponse, None),
                permission=Permission.REGION_DESCRIBE
            ),
            cls.route(
                Endpoint.REGIONS_NAME,
                HTTPMethod.GET,
                'get',
                response=(HTTPStatus.OK, RegionResponse, None),
                permission=Permission.REGION_DESCRIBE
            ),
            cls.route(
                Endpoint.REGIONS,
                HTTPMethod.POST,
                'post',
                response=(HTTPStatus.CREATED, RegionResponse, None),
                permission=Permission.REGION_CREATE
            ),
            cls.route(
                Endpoint.REGIONS_NAME,
                HTTPMethod.DELETE,
                'delete',
                response=(HTTPStatus.NO_CONTENT, None, None),
                permission=Permission.REGION_DELETE
            ),
        )

    @validate_kwargs
    def get(self, event: BaseModel, name: str):
        item = self.region_service.get_region(region_name=name)
        if not item:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'Region not found'
            ).exc()
        return build_response(content=self.region_service.get_dto(item))

    @validate_kwargs
    def query(self, event: BaseModel):

        _LOG.debug('Describing all regions')
        # TODO for modular-sdk -> rewrite get_all_regions
        regions = self.region_service.get_all_regions(only_active=False)

        return build_response(
            content=map(self.region_service.get_dto, regions)
        )

    @validate_kwargs
    def post(self, event: RegionPost):

        maestro_name = event.maestro_name
        existing_region = self.region_service.get_region(
            region_name=maestro_name)
        if existing_region:
            _LOG.error(f'Region {maestro_name} already exists.')
            raise ResponseFactory(HTTPStatus.CONFLICT).message(
                f'Region {maestro_name} already exists.'
            ).exc()

        _LOG.debug('Creating region')
        region = self.region_service.create(
            maestro_name=maestro_name,
            native_name=event.native_name,
            region_id=event.region_id,
            cloud=event.cloud,
            is_active=True
        )
        _LOG.debug('Saving region')
        self.region_service.save(region_item=region)

        return build_response(content=self.region_service.get_dto(region))

    @validate_kwargs
    def delete(self, event: BaseModel, name: str):

        region = self.region_service.get_region(name)
        if not region:
            return build_response(code=HTTPStatus.NO_CONTENT)

        self.region_service.delete(region=region)

        return build_response(code=HTTPStatus.NO_CONTENT)
