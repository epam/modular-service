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
from services.region_mutator_service import RegionMutatorService
from services.tenant_mutator_service import TenantMutatorService
from validators.request import RegionDelete, RegionGet, RegionPost
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
    def routes(cls) -> list[Route]:
        name = cls.controller_name()
        endpoint = Endpoint.REGIONS.value
        return [
            Route(None, endpoint, controller=name, action='get',
                  conditions={'method': [HTTPMethod.GET]}),
            Route(None, endpoint, controller=name, action='post',
                  conditions={'method': [HTTPMethod.POST]}),
            Route(None, endpoint, controller=name, action='delete',
                  conditions={'method': [HTTPMethod.DELETE]}),
        ]

    @validate_kwargs
    def get(self, event: RegionGet):

        maestro_name = event.maestro_name

        if maestro_name:
            _LOG.debug(f'Describing region by maestro name \'{maestro_name}\'')
            regions = [self.region_service.get_region(region_name=maestro_name)]
        else:
            _LOG.debug('Describing all regions')
            regions = self.region_service.get_all_regions(only_active=False)

        regions = [item for item in regions if item]
        if not regions:
            _LOG.warning('No regions found matching given query')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'No regions found matching given query'
            ).exc()

        _LOG.debug('Extracting region dto')
        response = [self.region_service.get_dto(region=region)
                    for region in regions]
        _LOG.debug(f'Response: {response}')
        return build_response(content=response)

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

        _LOG.debug('Extracting region dto')
        response = self.region_service.get_dto(region=region)
        _LOG.debug(f'Response: {response}')
        return build_response(content=response)

    @validate_kwargs
    def delete(self, event: RegionDelete):
        region_name = event.maestro_name

        region = self.region_service.get_region(
            region_name=region_name)
        if not region:
            _LOG.warning(f'Region {region_name} does not exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Region {region_name} does not exist.'
            ).exc()

        _LOG.warning(f'Going to remove region {region_name}')
        self.region_service.delete(region=region)

        _LOG.debug(f'Region \'{region_name}\' has been removed')
        return build_response(content=f'Region \'{region_name}\' has been removed')
