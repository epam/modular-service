import os
from enum import Enum
from typing import Iterator, MutableMapping

from typing_extensions import Self


# from http import HTTPMethod  # python3.11+

class HTTPMethod(str, Enum):
    HEAD = 'HEAD'
    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    PUT = 'PUT'


class Endpoint(str, Enum):
    DOC = '/doc'
    ROLES = '/roles'
    USERS = '/users'
    SIGNUP = '/signup'
    SIGNIN = '/signin'
    TENANTS = '/tenants'
    REGIONS = '/regions'
    PARENTS = '/parents'
    REFRESH = '/refresh'
    POLICIES = '/policies'
    CUSTOMERS = '/customers'
    HEALTH_LIVE = '/health/live'
    ROLES_NAME = '/roles/{name}'
    USERS_WHOAMI = '/users/whoami'
    APPLICATIONS = '/applications'
    TENANTS_NAME = '/tenants/{name}'
    REGIONS_NAME = '/regions/{name}'  # maestro name
    POLICIES_NAME = '/policies/{name}'
    USERS_USERNAME = '/users/{username}'
    CUSTOMERS_NAME = '/customers/{name}'
    APPLICATIONS_ID = '/applications/{id}'
    DOC_SWAGGER_JSON = '/doc/swagger.json'
    USERS_RESET_PASSWORD = '/users/reset-password'
    TENANTS_NAME_REGIONS = '/tenants/{name}/regions'
    APPLICATIONS_AWS_ROLE = '/applications/aws-role'
    TENANTS_NAME_SETTINGS = '/tenants/{name}/settings'
    TENANTS_NAME_ACTIVATE = '/tenants/{name}/activate'
    TENANTS_NAME_DEACTIVATE = '/tenants/{name}/deactivate'
    CUSTOMERS_NAME_ACTIVATE = '/customers/{name}/activate'
    CUSTOMERS_NAME_DEACTIVATE = '/customers/{name}/deactivate'
    APPLICATIONS_AWS_CREDENTIALS = '/applications/aws-credentials'
    APPLICATIONS_AZURE_CREDENTIALS = '/applications/azure-credentials'
    APPLICATIONS_AZURE_CERTIFICATE = '/applications/azure-certificate'
    APPLICATIONS_GCP_SERVICE_ACCOUNT = '/applications/gcp-service-account'

    @classmethod
    def match(cls, resource: str) -> Self | None:
        """
        Tries to resolve endpoint from our enum from Api Gateway resource.
        Enum contains endpoints without stage. Though in general trailing
        slashes matter and endpoints with and without such slash are
        considered different we ignore this and consider such paths equal:
        - /path/to/resource
        - /path/to/resource/
        This method does the following:
        >>> Endpoint.match('/roles') == Endpoint.ROLES
        >>> Endpoint.match('roles') == Endpoint.ROLES
        >>> Endpoint.match('roles/') == Endpoint.ROLES
        :param resource:
        :return:
        """
        raw = resource.strip('/')  # without trailing slashes
        for case in (raw, f'/{raw}', f'{raw}/', f'/{raw}/'):
            try:
                return cls(case)
            except ValueError:
                pass
        return


_SENTINEL = object()


class Env(str, Enum):
    """
    Collection of available environment variables
    """

    default: str | None

    @staticmethod
    def source() -> MutableMapping:
        return os.environ

    def __new__(cls, value: str, default: str | None = None):
        """
        All environment variables and optionally their default values.
        Since envs always have string type the default value also should be
        of string type and then converted to the necessary type in code.
        There is no default value if not specified (default equal to unset)
        """
        obj = str.__new__(cls, value)
        obj._value_ = value

        obj.default = default
        return obj

    def get(self, default=_SENTINEL) -> str | None:
        if default is _SENTINEL:
            default = self.default
        if default is not None:
            default = str(default)
        return self.source().get(self.value, default)

    def set(self, val: str | None):
        if val is None:
            self.source().pop(self.value, None)
        else:
            self.source()[self.value] = str(val)

    # internal envs
    INVOCATION_REQUEST_ID = '_INVOCATION_REQUEST_ID'

    # external envs
    AWS_REGION = 'AWS_REGION', 'us-east-1'
    SERVICE_MODE = 'MODULAR_SERVICE_MODE', 'saas'
    LOG_LEVEL = 'MODULAR_SERVICE_LOG_LEVEL', 'INFO'
    COGNITO_USER_POOL_NAME = 'MODULAR_SERVICE_COGNITO_USER_POOL_NAME'
    COGNITO_USER_POOL_ID = 'MODULAR_SERVICE_COGNITO_USER_POOL_ID'

    VAULT_ENDPOINT = 'MODULAR_SERVICE_VAULT_ENDPOINT'
    VAULT_TOKEN = 'MODULAR_SERVICE_VAULT_TOKEN'

    MONGO_URI = 'MODULAR_SERVICE_MONGO_URI'
    MONGO_DATABASE = 'MODULAR_SERVICE_MONGO_DATABASE', 'modular_service'

    EXTERNAL_SSM = 'MODULAR_SERVICE_USE_EXTERNAL_SSM'

    SYSTEM_USER_PASSWORD = 'MODULAR_SERVICE_SYSTEM_USER_PASSWORD'

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    @classmethod
    def is_docker(cls) -> bool:
        return cls.SERVICE_MODE.get() == 'docker'


class Permission(str, Enum):
    """
    Collection of all available rbac permissions
    """
    APPLICATION_DESCRIBE = 'application:describe'
    APPLICATION_CREATE = 'application:create'
    APPLICATION_UPDATE = 'application:update'
    APPLICATION_DELETE = 'application:delete'

    CUSTOMER_DESCRIBE = 'customer:describe'
    CUSTOMER_CREATE = 'customer:create'
    CUSTOMER_UPDATE = 'customer:update'
    CUSTOMER_ACTIVATE = 'customer:activate'
    CUSTOMER_DEACTIVATE = 'customer:deactivate'

    PARENT_DESCRIBE = 'parent:describe'
    PARENT_CREATE = 'parent:create'
    PARENT_UPDATE = 'parent:update'
    PARENT_DELETE = 'parent:delete'

    TENANT_DESCRIBE = 'tenant:describe'
    TENANT_CREATE = 'tenant:create'
    TENANT_UPDATE = 'tenant:update'
    TENANT_DELETE = 'tenant:delete'
    TENANT_ACTIVATE = 'tenant:activate'
    TENANT_DEACTIVATE = 'tenant:deactivate'
    TENANT_CREATE_REGION = 'tenant:create_region'
    TENANT_DESCRIBE_REGION = 'tenant:describe_region'
    TENANT_DELETE_REGION = 'tenant:delete_region'

    REGION_DESCRIBE = 'region:describe'
    REGION_CREATE = 'region:create'
    REGION_DELETE = 'region:delete'

    ROLE_DESCRIBE = 'role:describe'
    ROLE_CREATE = 'role:create'
    ROLE_UPDATE = 'role:update'
    ROLE_DELETE = 'role:delete'

    POLICY_DESCRIBE = 'policy:describe'
    POLICY_CREATE = 'policy:create'
    POLICY_UPDATE = 'policy:update'
    POLICY_DELETE = 'policy:delete'

    TENANT_SETTING_SET = 'tenant_setting:set'
    TENANT_SETTING_DESCRIBE = 'tenant_setting:describe'

    USERS_DESCRIBE = 'users:describe'
    USERS_CREATE = 'users:create'
    USERS_UPDATE = 'users:update'
    USERS_DELETE = 'users:delete'
    USERS_GET_CALLER = 'users:get_caller'
    USERS_RESET_PASSWORD = 'users:reset_password'

    def __str__(self):
        return self.value

    @classmethod
    def hidden(cls) -> set[Self]:
        """
        These are permissions that are currently hidden for standard users
        meaning that endpoints behind these permission cannot be used by
        standard users. Only system user can use those endpoints, though
        permissions are not checked for system.
        :return:
        """
        return {
            cls.REGION_DELETE,
            cls.REGION_CREATE,
            cls.CUSTOMER_CREATE
        }

    @classmethod
    def iter_all(cls) -> Iterator[Self]:
        """
        Iterates over all the currently available permission
        :return:
        """
        hidden = cls.hidden()
        return filter(lambda p: p not in hidden, cls)


LAMBDA_URL_HEADER_CONTENT_TYPE_UPPER = 'Content-Type'
JSON_CONTENT_TYPE = 'application/json'

TYPE_ATTR = 'type'
DESCRIPTION_ATTR = 'description'
APPLICATION_ID_ATTR = 'application_id'
PARENT_ID_ATTR = 'parent_id'

# standard for wsgi applications
REQUEST_METHOD_WSGI_ENV = 'REQUEST_METHOD'
PRIVATE_KEY_SECRET_NAME = 'modular-service-private-key'

# cognito
COGNITO_USERNAME = 'cognito:username'
COGNITO_SUB = 'sub'
CUSTOM_ROLE_ATTR = 'custom:modular_role'
CUSTOM_IS_SYSTEM = 'custom:is_system'
CUSTOM_CUSTOMER_ATTR = 'custom:customer'
CUSTOM_LATEST_LOGIN_ATTR = 'custom:latest_login'
