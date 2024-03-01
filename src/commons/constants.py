import operator
from enum import Enum
from typing import Iterator

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
    ROLES = '/roles'
    SIGNUP = '/signup'
    SIGNIN = '/signin'
    TENANTS = '/tenants'
    REGIONS = '/regions'
    PARENTS = '/parents'
    POLICIES = '/policies'
    CUSTOMERS = '/customers'
    ROLES_NAME = '/roles/{name}'
    APPLICATIONS = '/applications'
    TENANTS_NAME = '/tenants/{name}'
    POLICIES_NAME = '/policies/{name}'
    CUSTOMERS_NAME = '/customers/{name}'
    TENANTS_REGIONS = '/tenants/regions'
    APPLICATIONS_ID = '/applications/{id}'
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


class Env(str, Enum):
    """
    Collection of available environment variables
    """
    # internal envs
    INVOCATION_REQUEST_ID = '_INVOCATION_REQUEST_ID'

    # deprecated envs, but still can be used, but should NOT be used
    OLD_SERVICE_MODE = 'service_mode'
    OLD_COGNITO_USER_POOL_NAME = 'cognito_user_pool_name'
    OLD_COGNITO_USER_POOL_ID = 'user_pool_id'
    OLD_VAULT_TOKEN = 'VAULT_TOKEN'
    OLD_VAULT_URL = 'VAULT_URL'
    OLD_VAULT_PORT = 'VAULT_SERVICE_SERVICE_PORT'

    # external envs
    AWS_REGION = 'AWS_REGION'
    SERVICE_MODE = 'MODULAR_SERVICE_MODE'
    LOG_LEVEL = 'MODULAR_SERVICE_LOG_LEVEL'
    COGNITO_USER_POOL_NAME = 'MODULAR_SERVICE_COGNITO_USER_POOL_NAME'
    COGNITO_USER_POOL_ID = 'MODULAR_SERVICE_COGNITO_USER_POOL_ID'

    VAULT_ENDPOINT = 'MODULAR_SERVICE_VAULT_ENDPOINT'
    VAULT_TOKEN = 'MODULAR_SERVICE_VAULT_TOKEN'

    MONGO_URI = 'MODULAR_SERVICE_MONGO_URI'
    MONGO_DATABASE = 'MODULAR_SERVICE_MONGO_DATABASE'

    EXTERNAL_SSM = 'MODULAR_SERVICE_USE_EXTERNAL_SSM'

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


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
    CUSTOMER_DELETE = 'customer:delete'
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

    @classmethod
    def all(cls) -> Iterator[str]:
        return map(operator.attrgetter('value'), cls)


LAMBDA_URL_HEADER_CONTENT_TYPE_UPPER = 'Content-Type'
JSON_CONTENT_TYPE = 'application/json'

NAME_ATTR = 'name'

EXPIRATION_ATTR = 'expiration'
PERMISSIONS_ATTR = 'permissions'
POLICIES_ATTR = 'policies'

TYPE_ATTR = 'type'
DESCRIPTION_ATTR = 'description'
APPLICATION_ID_ATTR = 'application_id'
PARENT_ID_ATTR = 'parent_id'

# standard for wsgi applications
REQUEST_METHOD_WSGI_ENV = 'REQUEST_METHOD'
PRIVATE_KEY_SECRET_NAME = 'modular-service-private-key'
