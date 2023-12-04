import os

from modular_sdk.modular import Modular

from commons import SingletonMeta
from connections.auth_extension.base_auth_client import AuthClient
from connections.vault_extension.base_secrets_client import BaseSecretsClient
from services.application_mutator_service import ApplicationMutatorService
from services.clients.cognito import CognitoClient
from services.customer_mutator_service import CustomerMutatorService
from services.environment_service import EnvironmentService
from services.parent_mutator_service import ParentMutatorService
from services.rbac.access_control_service import AccessControlService
from services.rbac.iam_service import IamService
from services.region_mutator_service import RegionMutatorService
from services.setting_service import SettingsService
from services.ssm_service import SSMService
from services.tenant_mutator_service import TenantMutatorService
from services.user_service import CognitoUserService

SERVICE_MODE = os.getenv('service_mode')
is_docker = SERVICE_MODE == 'docker'


class ServiceProvider(metaclass=SingletonMeta):
    __modular = None
    __cognito_conn = None
    __ssm_conn = None

    # services
    __user_service = None
    __environment_service = None
    __settings_service = None
    __access_control_service = None
    __iam_service = None
    __ssm_service = None
    __application_mutator_service = None
    __parent_mutator_service = None
    __tenant_mutator_service = None
    __region_mutator_service = None
    __customer_mutator_service = None

    def __str__(self):
        return id(self)

    @property
    def modular(self) -> Modular:
        if not self.__modular:
            self.__modular = Modular()
        return self.__modular

    # clients
    def ssm(self):
        if not self.__ssm_conn:
            self.__ssm_conn = BaseSecretsClient(
                region=self.environment_service().aws_region())
        return self.__ssm_conn

    def cognito(self):
        if not self.__cognito_conn:
            if is_docker:
                from connections.auth_extension.cognito_to_jwt_adapter \
                    import CognitoToJWTAdapter
                self.__cognito_conn = AuthClient(CognitoToJWTAdapter(
                    storage_service=self.ssm_service())
                )
            else:
                self.__cognito_conn = CognitoClient(
                    environment_service=self.environment_service())
        return self.__cognito_conn

    # services

    def user_service(self):
        if not self.__user_service:
            self.__user_service = CognitoUserService(
                client=self.cognito())
        return self.__user_service

    def ssm_service(self):
        if not self.__ssm_service:
            self.__ssm_service = SSMService(client=self.ssm())
        return self.__ssm_service

    def environment_service(self):
        if not self.__environment_service:
            self.__environment_service = EnvironmentService()
        return self.__environment_service

    def settings_service(self):
        if not self.__settings_service:
            self.__settings_service = SettingsService()
        return self.__settings_service

    def access_control_service(self):
        if not self.__access_control_service:
            self.__access_control_service = AccessControlService(
                iam_service=self.iam_service(),
                user_service=self.user_service(),
                setting_service=self.settings_service()
            )
        return self.__access_control_service

    def iam_service(self):
        if not self.__iam_service:
            self.__iam_service = IamService()
        return self.__iam_service

    def application_service(self):
        if not self.__application_mutator_service:
            self.__application_mutator_service = \
                ApplicationMutatorService(self.customer_service())
        return self.__application_mutator_service

    def customer_service(self):
        if not self.__customer_mutator_service:
            self.__customer_mutator_service = CustomerMutatorService()
        return self.__customer_mutator_service

    def parent_service(self):
        if not self.__parent_mutator_service:
            self.__parent_mutator_service = ParentMutatorService(
                application_service=self.application_service(),
                tenant_service=self.tenant_service(),
                customer_service=self.customer_service()
            )
        return self.__parent_mutator_service

    def region_service(self):
        if not self.__region_mutator_service:
            self.__region_mutator_service = RegionMutatorService(
                self.tenant_service()
            )
        return self.__region_mutator_service

    def tenant_service(self):
        if not self.__tenant_mutator_service:
            self.__tenant_mutator_service = TenantMutatorService(
                self.customer_service())
        return self.__tenant_mutator_service

    def reset(self, service: str):
        """Removes the saved instance of the service. It is useful,
        for example, in case of gitlab service - when we want to use
        different rule-sources configurations"""
        private_service_name = f'_ServiceProvider__{service}'
        if not hasattr(self, private_service_name):
            raise AssertionError(
                f'In case you are using this method, make sure your '
                f'service {private_service_name} exists amongst the '
                f'private attributes')
        setattr(self, private_service_name, None)
