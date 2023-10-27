from typing import List

from routes.route import Route

from commons import validate_params, build_response, RESPONSE_BAD_REQUEST_CODE, \
    generate_id, RESPONSE_OK_CODE, RESPONSE_RESOURCE_NOT_FOUND_CODE
from commons.constants import GET_METHOD, POST_METHOD, DELETE_METHOD, \
    MAESTRO_NAME_ATTR, NATIVE_NAME_ATTR, REGION_ID_ATTR, CLOUD_ATTR
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import \
    AbstractCommandProcessor
from services import SERVICE_PROVIDER
from services.region_mutator_service import RegionMutatorService
from services.tenant_mutator_service import TenantMutatorService

_LOG = get_logger(__name__)


class RegionProcessor(AbstractCommandProcessor):
    def __init__(self, tenant_service: TenantMutatorService,
                 region_service: RegionMutatorService):
        self.tenant_service: TenantMutatorService = tenant_service
        self.region_service: RegionMutatorService = region_service

    @classmethod
    def build(cls) -> 'RegionProcessor':
        return cls(
            tenant_service=SERVICE_PROVIDER.tenant_service(),
            region_service=SERVICE_PROVIDER.region_service()
        )

    @classmethod
    def routes(cls) -> List[Route]:
        name = cls.controller_name()
        return [
            Route(None, '/regions', controller=name, action='get',
                  conditions={'method': [GET_METHOD]}),
            Route(None, '/regions', controller=name, action='post',
                  conditions={'method': [POST_METHOD]}),
            Route(None, '/regions', controller=name, action='delete',
                  conditions={'method': [DELETE_METHOD]}),
        ]

    def get(self, event):
        _LOG.debug(f'Describe region event: {event}')

        maestro_name = event.get(MAESTRO_NAME_ATTR)

        if maestro_name:
            _LOG.debug(f'Describing region by maestro name \'{maestro_name}\'')
            regions = [self.region_service.get_region(region_name=maestro_name)]
        else:
            _LOG.debug(f'Describing all regions')
            regions = self.region_service.get_all_regions(only_active=False)

        regions = [item for item in regions if item]
        if not regions:
            _LOG.error(f'No regions found matching given query')
            return build_response(
                code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                content=f'No regions found matching given query'
            )

        _LOG.debug(f'Extracting region dto')
        response = [self.region_service.get_dto(region=region)
                    for region in regions]
        _LOG.debug(f'Response: {response}')
        return build_response(
            code=RESPONSE_OK_CODE,
            content=response
        )

    def post(self, event):
        _LOG.debug(f'Add region event: {event}')
        validate_params(event,
                        (MAESTRO_NAME_ATTR, NATIVE_NAME_ATTR, CLOUD_ATTR))

        maestro_name = event.get(MAESTRO_NAME_ATTR)
        existing_region = self.region_service.get_region(
            region_name=maestro_name)
        if existing_region:
            _LOG.error(f'Region {maestro_name} already exists.')
            return build_response(
                code=RESPONSE_BAD_REQUEST_CODE,
                content=f'Region {maestro_name} already exists.')

        region_id = event.get(REGION_ID_ATTR)
        cloud = event.get(CLOUD_ATTR)
        native_name = event.get(NATIVE_NAME_ATTR)
        region_id = region_id if region_id else generate_id()

        _LOG.debug(f'Creating region')
        region = self.region_service.create(
            maestro_name=maestro_name,
            native_name=native_name,
            region_id=region_id,
            cloud=cloud,
            is_active=True
        )
        _LOG.debug(f'Saving region')
        self.region_service.save(region_item=region)

        _LOG.debug(f'Extracting region dto')
        response = self.region_service.get_dto(region=region)
        _LOG.debug(f'Response: {response}')
        return build_response(
            code=RESPONSE_OK_CODE,
            content=response
        )

    def delete(self, event):
        _LOG.debug(f'Delete region event: {event}')
        validate_params(event, (MAESTRO_NAME_ATTR,))

        region_name = event.get(MAESTRO_NAME_ATTR)

        region = self.region_service.get_region(
            region_name=region_name)
        if not region:
            _LOG.error(f'Region {region_name} does not exist.')
            return build_response(
                code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                content=f'Region {region_name} does not exist.')

        _LOG.warning(f'Going to remove region {region_name}')
        self.region_service.delete(region=region)

        _LOG.debug(f'Region \'{region_name}\' has been removed')
        return build_response(
            code=RESPONSE_OK_CODE,
            content=f'Region \'{region_name}\' has been removed'
        )
