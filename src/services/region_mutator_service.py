from typing import Optional
from http import HTTPStatus

from bson import ObjectId

from commons.log_helper import get_logger
from modular_sdk.commons import ModularException
from modular_sdk.commons.constants import CLOUD_PROVIDERS
from modular_sdk.models.region import RegionModel, RegionAttr
from modular_sdk.models.tenant import Tenant
from modular_sdk.services.region_service import RegionService
from modular_sdk.services.tenant_service import TenantService

_LOG = get_logger(__name__)


class RegionMutatorService(RegionService):
    def __init__(self, tenant_service: TenantService):
        super().__init__(tenant_service=tenant_service)

    def create_light(self, maestro_name: str, native_name: str, cloud: str,
                     region_id: Optional[str] = None,
                     is_active: Optional[bool] = True):
        """
        Without whole-table scans.
        Judging by dev2 tables, region_id highly resembles MongoDB's ObjectId.
        So, it's always unique, and we need not check collisions.
        If you pass region_id, make sure it's unique or just let us generate it
        """
        assert cloud in CLOUD_PROVIDERS, 'Invalid cloud'
        by_native_name = self.get_region_by_native_name(native_name, cloud)
        if by_native_name:
            raise ModularException(
                code=HTTPStatus.CONFLICT.value,
                content=f'Region {native_name} already exists in db'
            )
        by_maestro_name = self.get_region(maestro_name)
        if by_maestro_name:
            raise ModularException(
                code=HTTPStatus.CONFLICT.value,
                content=f'Region {maestro_name} already exists in db'
            )
        return RegionModel(
            maestro_name=maestro_name,
            native_name=native_name,
            cloud=cloud,
            region_id=region_id or str(ObjectId()),
            is_active=is_active
        )

    def create(self, maestro_name: str, native_name: str, region_id: str,
               cloud: str, is_active=True):
        if cloud not in CLOUD_PROVIDERS:
            _LOG.error(f'Unsupported cloud specified: \'{cloud}\'. '
                       f'Available options: {CLOUD_PROVIDERS}')
            raise ModularException(
                code=HTTPStatus.BAD_REQUEST.value,
                content=f'Unsupported cloud specified: \'{cloud}\'. '
                        f'Available options: {CLOUD_PROVIDERS}'
            )
        all_region = self.get_all_regions()
        # todo rewrite this, why should we scan all regions when creating and not even saving one?
        if region_id:
            for region in all_region:
                if region.region_id == region_id and \
                        maestro_name != region.maestro_name:
                    _LOG.error(f'The region id {region_id} is already used by '
                               f'the {region.maestro_name} region.')
                    raise ModularException(
                        code=HTTPStatus.BAD_REQUEST.value,
                        content=f'The region id {region_id} is already used by'
                                f' the {region.maestro_name} region.')
        all_region_in_cloud = [region for region in all_region
                               if region.cloud == cloud]
        for region in all_region_in_cloud:
            if region.native_name == native_name and \
                    maestro_name != region.maestro_name:
                _LOG.error(f'The native name {native_name} is already '
                           f'used by the {region.maestro_name} region.')
                raise ModularException(
                    code=HTTPStatus.BAD_REQUEST.value,
                    content=f'The native name {native_name} is already '
                            f'used by the {region.maestro_name} region.')
        return RegionModel(
            region_id=region_id, maestro_name=maestro_name,
            native_name=native_name, cloud=cloud,
            is_active=is_active
        )

    def delete(self, region: RegionModel):
        tenants = self.tenant_service.scan_tenants(
            only_active=True)  # TODO 7000 tenants on prod...
        _LOG.debug(f'Searching for activated tenants in region '
                   f'\'{region.maestro_name}\'')
        activated_tenants = []
        for tenant in tenants:
            if tenant.regions:
                for tenant_region in tenant.regions:
                    if tenant_region.maestro_name == region.maestro_name:
                        activated_tenants.append(tenant.name)
        if activated_tenants:
            raise ModularException(
                code=HTTPStatus.BAD_REQUEST.value,
                content=f'There are activated tenants '
                        f'{activated_tenants} in region {region.maestro_name}')
        region.delete()

    def activate_region_in_tenant(self, tenant: Tenant, region: RegionModel):
        region = self.region_model_to_attr(region)
        if tenant.regions:
            if self.check_region_is_not_activated(
                    region_to_add=region,
                    tenant_regions=tenant.regions):
                _LOG.debug(f'Region \'{region.maestro_name}\' added to tenant '
                           f'\'{tenant.name}\'')
                tenant.regions.append(region)
            else:
                raise ModularException(
                    code=HTTPStatus.BAD_REQUEST.value,
                    content=f'Region {region.maestro_name} is already '
                            f'activated'
                )
        else:
            tenant.regions = [region]

    @staticmethod
    def delete_region_from_tenant(tenant: Tenant, region: RegionModel):
        if not tenant.regions:
            _LOG.error(f'Tenant \'{tenant.name}\' does not have any regions')
            raise ModularException(
                code=HTTPStatus.NOT_FOUND.value,
                content=f'Tenant \'{tenant.name}\' does not have any regions'
            )
        target_region = None
        for tenant_region in tenant.regions:
            if tenant_region.maestro_name == region.maestro_name:
                target_region = tenant_region

        if not target_region:
            _LOG.error(f'Region \'{region.maestro_name}\' does not exist in '
                       f'\'{tenant.name}\' tenant.')
            raise ModularException(
                code=HTTPStatus.NOT_FOUND.value,
                content=f'Region \'{region.maestro_name}\' does not exist in '
                        f'\'{tenant.name}\' tenant.'
            )

        if target_region and not target_region.is_active:
            _LOG.warning(f'Region \'{region.maestro_name}\' is already '
                         f'deactivated for tenant \'{tenant.name}\'.')
            raise ModularException(
                code=HTTPStatus.BAD_REQUEST.value,
                content=f'Region \'{region.maestro_name}\' is already '
                        f'deactivated for tenant \'{tenant.name}\'.'
            )

        _LOG.debug(f'Deactivating region \'{region.maestro_name}\' for '
                   f'tenant \'{tenant.name}\'')
        target_region.is_active = False

    @staticmethod
    def save(region_item):
        region_item.save()

    @staticmethod
    def update(region_item: RegionModel, actions: list) -> None:
        region_item.update(actions=actions)

    @staticmethod
    def deactivate(region: RegionAttr):
        region.is_active = False

