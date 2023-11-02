from commons.log_helper import get_logger
from modular_sdk.commons import ModularException, RESPONSE_RESOURCE_NOT_FOUND_CODE, \
    RESPONSE_BAD_REQUEST_CODE
from modular_sdk.commons.constants import CLOUD_PROVIDERS
from modular_sdk.commons.time_helper import utc_iso
from modular_sdk.models.tenant import Tenant
from modular_sdk.services.customer_service import CustomerService
from modular_sdk.services.tenant_service import TenantService

_LOG = get_logger('TenantService')


class TenantMutatorService(TenantService):
    def __init__(self, customer_service: CustomerService):
        super().__init__(customer_service=customer_service)

    def create(
            self, tenant_name: str, display_name: str, customer_name: str,
            cloud: str, acc: str, contacts: dict = None,
            is_active=True, read_only=False
    ):
        # TODO, what if I just create a tenant with existing name and
        #  override someone's data ?
        if cloud not in CLOUD_PROVIDERS:
            _LOG.error(f'Invalid cloud \'{cloud}\' specified. Available '
                       f'options: {CLOUD_PROVIDERS}')
            raise ModularException(
                code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                content=f'Invalid cloud \'{cloud}\' specified. Available '
                        f'options: {CLOUD_PROVIDERS}'
            )
        customer_exist = self.customer_service.get(name=customer_name)

        if not customer_exist:
            _LOG.error(f'Customer with name \'{customer_name}\' does not '
                       f'exist.')
            raise ModularException(
                code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                content=f'Customer with name \'{customer_name}\' does not '
                        f'exist.'
            )
        tenant = Tenant(
            name=tenant_name,
            display_name=display_name,
            display_name_to_lower=display_name.lower(),
            read_only=read_only,
            is_active=is_active,
            customer_name=customer_name,
            cloud=cloud,
            project=acc,
            contacts=contacts
        )
        tenant.activation_date = utc_iso()
        return tenant

    @staticmethod
    def remove(tenant: Tenant):
        tenant.delete()

    @staticmethod
    def mark_deactivated(tenant: Tenant):
        if not tenant.is_active:
            _LOG.warning(f'Tenant \'{tenant.name}\' is already deactivated.')
            # TODO wouldn't be better to return 200 here?
            raise ModularException(
                code=RESPONSE_BAD_REQUEST_CODE,
                content=f'Tenant \'{tenant.name}\' is already deactivated.'
            )
        if tenant.regions and any(region.is_active for region in tenant.regions):
            _LOG.error(f'Cannot deactivate {tenant.name} tenant because there '
                       f'are regions persists')
            raise ModularException(
                code=RESPONSE_BAD_REQUEST_CODE,
                content=f'Cannot deactivate {tenant.name} tenant '
                        f'because there are regions persists'
            )
        tenant.is_active = False

    @staticmethod
    def save(tenant: Tenant):
        tenant.save()

    @staticmethod
    def update(tenant_item: Tenant, actions: list) -> None:
        tenant_item.update(actions=actions)

