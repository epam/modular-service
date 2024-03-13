import os
from functools import cached_property
from typing import TYPE_CHECKING

from modular_sdk.modular import Modular

from commons import SingletonMeta

if TYPE_CHECKING:
    from modular_sdk.services.ssm_service import AbstractSSMClient
    from services.clients.cognito import BaseAuthClient
    from services.user_service import CognitoUserService
    from services.environment_service import EnvironmentService
    from services.parent_mutator_service import ParentMutatorService
    from services.customer_mutator_service import CustomerMutatorService
    from services.rbac_service import RBACService
    from services.region_mutator_service import RegionMutatorService
    from services.tenant_mutator_service import TenantMutatorService


class ServiceProvider(metaclass=SingletonMeta):
    @cached_property
    def modular(self) -> Modular:
        return Modular()

    # clients
    @cached_property
    def ssm(self) -> 'AbstractSSMClient':
        if self.environment_service.is_docker():
            from services.clients.ssm import ModularVaultSSMClient
            return ModularVaultSSMClient(
                environment_service=self.environment_service
            )
        if self.environment_service.is_external_ssm():
            return self.modular.assume_role_ssm_service()
        else:
            return self.modular.ssm_service()

    @cached_property
    def cognito(self) -> 'BaseAuthClient':
        if self.environment_service.is_docker():
            from services.clients.mongo_ssm_auth_client import \
                MongoAndSSMAuthClient
            return MongoAndSSMAuthClient(ssm_client=self.ssm)
        from services.clients.cognito import CognitoClient
        return CognitoClient(environment_service=self.environment_service)

    # services
    @cached_property
    def user_service(self) -> 'CognitoUserService':
        from services.user_service import CognitoUserService
        return CognitoUserService(client=self.cognito)

    @cached_property
    def environment_service(self) -> 'EnvironmentService':
        from services.environment_service import EnvironmentService
        return EnvironmentService(os.environ)

    @cached_property
    def customer_service(self) -> 'CustomerMutatorService':
        from services.customer_mutator_service import CustomerMutatorService
        return CustomerMutatorService()

    @cached_property
    def parent_service(self) -> 'ParentMutatorService':
        from services.parent_mutator_service import ParentMutatorService
        return ParentMutatorService(
            application_service=self.modular.application_service(),
            tenant_service=self.tenant_service,
            customer_service=self.customer_service
        )

    @cached_property
    def region_service(self) -> 'RegionMutatorService':
        from services.region_mutator_service import RegionMutatorService
        return RegionMutatorService(
            tenant_service=self.tenant_service
        )

    @cached_property
    def tenant_service(self) -> 'TenantMutatorService':
        from services.tenant_mutator_service import TenantMutatorService
        return TenantMutatorService()

    @cached_property
    def rbac_service(self) -> 'RBACService':
        from services.rbac_service import RBACService
        return RBACService()
