from enum import Enum

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
    APPLICATIONS = '/applications'
    TENANTS_REGIONS = '/tenants/regions'

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
    COGNITO_USER_POOL_NAME = 'MODULAR_SERVICE_COGNITO_USER_POOL_NAME'
    COGNITO_USER_POOL_ID = 'MODULAR_SERVICE_COGNITO_USER_POOL_ID'

    VAULT_ENDPOINT = 'MODULAR_SERVICE_VAULT_ENDPOINT'
    VAULT_TOKEN = 'MODULAR_SERVICE_VAULT_TOKEN'

    MONGO_URI = 'MODULAR_SERVICE_MONGO_URI'
    MONGO_DATABASE = 'MODULAR_SERVICE_MONGO_DATABASE'

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


LAMBDA_URL_HEADER_CONTENT_TYPE_UPPER = 'Content-Type'
JSON_CONTENT_TYPE = 'application/json'

ID_ATTR = 'id'
USERNAME_ATTR = 'username'
PASSWORD_ATTR = 'password'
ROLE_ATTR = 'role'
USER_ID_ATTR = 'user_id'
NAME_ATTR = 'name'
DISPLAY_NAME_ATTR = 'display_name'
ADMINS_ATTR = 'admins'
OVERRIDE_ATTR = 'override'
EMAILS_ATTR = 'emails'

SETTING_IAM_PERMISSIONS = 'IAM_PERMISSIONS'

BODY_ATTR = 'body'
EXPIRATION_ATTR = 'expiration'
PERMISSIONS_ATTR = 'permissions'
PERMISSIONS_ADMIN_ATTR = 'permissions_admin'
PERMISSIONS_TO_ATTACH = 'permissions_to_attach'
PERMISSIONS_TO_DETACH = 'permissions_to_detach'
POLICIES_TO_ATTACH = 'policies_to_attach'
POLICIES_TO_DETACH = 'policies_to_detach'
POLICIES_ATTR = 'policies'

TYPE_ATTR = 'type'
DESCRIPTION_ATTR = 'description'
CUSTOMER_ID_ATTR = 'customer_id'
APPLICATION_ID_ATTR = 'application_id'
PARENT_ID_ATTR = 'parent_id'
TENANT_CUSTOMER_ATTR = 'tenant_customer'
READ_ONLY_ATTR = 'read_only'
CLOUD_ATTR = 'cloud'
TENANT_ATTR = 'tenant'
REGION_ATTR = 'region'
HIDDEN_ATTR = 'hidden'

MAESTRO_NAME_ATTR = 'maestro_name'
NATIVE_NAME_ATTR = 'native_name'
REGION_ID_ATTR = 'region_id'

PARAM_ITEMS = 'items'
PARAM_MESSAGE = 'message'
SCOPE_ATTR = 'scope'

# standard for wsgi applications
REQUEST_METHOD_WSGI_ENV = 'REQUEST_METHOD'
REQUEST_PATH_WSGI_ENV = 'PATH_INFO'

META_ATTR = 'meta'

PARAM_REQUEST_CONTEXT = 'requestContext'
ID_TOKEN_ATTR = 'id_token'
REFRESH_TOKEN_ATTR = 'refresh_token'
PARAM_COGNITO_USERNAME = 'cognito:username'
PARAM_CUSTOM_ROLE = 'custom:modular_role'
PARAM_AUTHORIZER = 'authorizer'
PARAM_CLAIMS = 'claims'

PRIVATE_KEY_SECRET_NAME = 'modular-service-private-key'
