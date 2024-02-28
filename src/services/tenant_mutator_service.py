from typing import TypedDict

from modular_sdk.commons.constants import Cloud
from modular_sdk.commons.time_helper import utc_iso
from modular_sdk.models.tenant import Tenant
from modular_sdk.services.tenant_service import TenantService
from pynamodb.expressions.update import Action

from commons.log_helper import get_logger

_LOG = get_logger(__name__)


class Contacts(TypedDict):
    primary_contacts: list[str]
    secondary_contacts: list[str]
    tenant_manager_contacts: list[str]
    default_owner: str | None


class TenantMutatorService(TenantService):
    @staticmethod
    def create(tenant_name: str, display_name: str, customer_name: str,
               cloud: Cloud, acc: str, contacts: Contacts | None = None,
               is_active: bool = True, read_only: bool = False):
        tenant = Tenant(
            name=tenant_name,
            display_name=display_name,
            display_name_to_lower=display_name.lower(),
            read_only=read_only,
            is_active=is_active,
            customer_name=customer_name,
            cloud=cloud.value,
            project=acc,
            contacts=contacts,
            activation_date=utc_iso()
        )
        return tenant

    def activate(self, tenant: Tenant) -> None:
        if tenant.is_active:
            _LOG.debug('Tenant is already active. Returning')
            return
        self.update(
            tenant_item=tenant,
            actions=[
                Tenant.is_active.set(True),
                Tenant.activation_date.set(utc_iso()),
                Tenant.deactivation_date.set(None)
            ]
        )

    def deactivate(self, tenant: Tenant) -> None:
        if not tenant.is_active:
            _LOG.debug('Tenant is already not active. Returning')
            return
        self.update(
            tenant_item=tenant,
            actions=[
                Tenant.is_active.set(False),
                Tenant.deactivation_date.set(utc_iso())
            ]
        )

    @staticmethod
    def save(tenant: Tenant):
        tenant.save()

    @staticmethod
    def update(tenant_item: Tenant, actions: list[Action]) -> None:
        if actions:
            tenant_item.update(actions=actions)

    @staticmethod
    def remove(tenant: Tenant):
        tenant.delete()
