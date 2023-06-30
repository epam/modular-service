import json

import requests

from service.constants import *
from service.logger import get_logger, get_user_logger
from version import check_version_compatibility

HTTP_GET = 'get'
HTTP_POST = 'post'
HTTP_PATCH = 'patch'
HTTP_DELETE = 'delete'

ALLOWED_METHODS = [HTTP_GET, HTTP_POST, HTTP_PATCH, HTTP_DELETE]

SYSTEM_LOG = get_logger('modular_service_admin_cli.service.adapter_client')
USER_LOG = get_user_logger('user')


class AdapterClient:

    def __init__(self, adapter_api, token):
        self.__api_link = adapter_api
        self.__token = token
        self.__method_to_function = {
            HTTP_GET: requests.get,
            HTTP_POST: requests.post,
            HTTP_PATCH: requests.patch,
            HTTP_DELETE: requests.delete
        }
        SYSTEM_LOG.info('adapter SDK has been initialized')

    def __make_request(self, resource: str, method: str, payload: dict = None):
        if method not in ALLOWED_METHODS:
            SYSTEM_LOG.error(f'Requested method {method} in not allowed. '
                             f'Allowed methods: {ALLOWED_METHODS}')
            USER_LOG.error('Sorry, error happened. '
                           'Please contact the tool support team.')
        method_func = self.__method_to_function.get(method)
        parameters = dict(url=f'{self.__api_link}/{resource}')
        if method == HTTP_GET:
            parameters.update(params=payload)
        else:
            parameters.update(json=payload)
        SYSTEM_LOG.debug(f'API request info: {parameters}; Method: {method}')
        parameters.update(
            headers={'authorization': self.__token})
        try:
            response = method_func(**parameters)
        except requests.exceptions.ConnectionError:
            response = {
                'message': 'Provided configuration api_link is invalid '
                           'or outdated. Please contact the tool support team.'
            }
            return response
        SYSTEM_LOG.debug(f'API response info: {response}')
        return response

    def login(self, username, password):
        request = {
            PARAM_USERNAME: username,
            PARAM_PASSWORD: password
        }
        response = self.__make_request(
            resource=API_SIGNIN,
            method=HTTP_POST,
            payload=request
        )
        if isinstance(response, dict):
            return response
        if response.status_code != 200:
            if 'Incorrect username or password' in response.text:
                return {'message': 'Provided credentials are invalid.'}
            else:
                SYSTEM_LOG.error(f'Error: {response.text}')
                return {'message': 'Malformed response obtained. '
                                   'Please contact support team '
                                   'for assistance.'}
        response = response.json()
        check_version_compatibility(
            response.get('items')[0].pop(PARAM_API_VERSION, None))
        return response.get('items')[0].get('id_token')

    def policy_get(self, policy_name):
        request = {}
        if policy_name:
            request[PARAM_NAME] = policy_name
        return self.__make_request(resource=API_POLICY, method=HTTP_GET,
                                   payload=request)

    def policy_post(self, policy_name, permissions,
                    permissions_admin, path_to_permissions):
        request = {PARAM_NAME: policy_name}
        if permissions:
            request[PARAM_PERMISSIONS] = permissions
        if permissions_admin:
            request[PARAM_PERMISSIONS_ADMIN] = True
        if path_to_permissions:
            content = self.__get_permissions_from_file(path_to_permissions)
            if isinstance(content, dict):
                return content
            if request.get(PARAM_PERMISSIONS):
                request[PARAM_PERMISSIONS].extend(content)
            else:
                request[PARAM_PERMISSIONS] = content
        return self.__make_request(resource=API_POLICY, method=HTTP_POST,
                                   payload=request)

    @staticmethod
    def __get_permissions_from_file(path_to_permissions):
        try:
            with open(path_to_permissions, 'r') as file:
                content = json.loads(file.read())
        except json.decoder.JSONDecodeError:
            return {'message': 'Invalid file content'}
        if not isinstance(content, list):
            return {'message': 'Invalid file content'}
        return content

    def policy_patch(self, policy_name, attach_permissions,
                     detach_permissions):
        request = {PARAM_NAME: policy_name}
        if attach_permissions:
            request[PERMISSIONS_TO_ATTACH] = attach_permissions
        if detach_permissions:
            request[PERMISSIONS_TO_DETACH] = detach_permissions
        return self.__make_request(resource=API_POLICY, method=HTTP_PATCH,
                                   payload=request)

    def policy_delete(self, policy_name):
        request = {PARAM_NAME: policy_name}
        return self.__make_request(resource=API_POLICY, method=HTTP_DELETE,
                                   payload=request)

    def role_get(self, role_name):
        request = {}
        if role_name:
            request[PARAM_NAME] = role_name
        return self.__make_request(resource=API_ROLE, method=HTTP_GET,
                                   payload=request)

    def role_post(self, role_name, expiration, policies):
        request = {PARAM_NAME: role_name,
                   PARAM_POLICIES: policies}
        if expiration:
            request[PARAM_EXPIRATION] = expiration
        return self.__make_request(resource=API_ROLE, method=HTTP_POST,
                                   payload=request)

    def role_patch(self, role_name, expiration,
                   attach_policies,
                   detach_policies):
        request = {PARAM_NAME: role_name}
        if expiration:
            request[PARAM_EXPIRATION] = expiration
        if attach_policies:
            request[POLICIES_TO_ATTACH] = attach_policies
        if detach_policies:
            request[POLICIES_TO_DETACH] = detach_policies
        request = {k: v for k, v in request.items() if v}
        return self.__make_request(resource=API_ROLE, method=HTTP_PATCH,
                                   payload=request)

    def role_delete(self, role_name):
        request = {PARAM_NAME: role_name}
        return self.__make_request(resource=API_ROLE, method=HTTP_DELETE,
                                   payload=request)

    def customer_get(self, name=None):
        request = {}
        if name:
            request[PARAM_NAME] = name
        return self.__make_request(resource=API_CUSTOMER, method=HTTP_GET,
                                   payload=request)

    def customer_post(self, name, display_name, admins=None):
        request = {
            PARAM_NAME: name,
            PARAM_DISPLAY_NAME: display_name
        }
        if admins:
            request[PARAM_ADMINS] = admins
        return self.__make_request(resource=API_CUSTOMER, method=HTTP_POST,
                                   payload=request)

    def customer_patch(self, name, admins, override=False):
        request = {
            PARAM_NAME: name,
            PARAM_ADMINS: admins,
            PARAM_OVERRIDE: override
        }
        return self.__make_request(resource=API_CUSTOMER, method=HTTP_PATCH,
                                   payload=request)

    def application_get(self, application_id=None):
        request = {}
        if application_id:
            request[PARAM_APPLICATION_ID] = application_id
        return self.__make_request(resource=API_APPLICATION, method=HTTP_GET,
                                   payload=request)

    def application_post(self, application_type, customer_id,
                         description=None):
        request = {
            PARAM_TYPE: application_type,
            PARAM_CUSTOMER_ID: customer_id
        }

        if description:
            request[PARAM_DESCRIPTION] = description
        return self.__make_request(resource=API_APPLICATION, method=HTTP_POST,
                                   payload=request)

    def application_patch(self, application_id, application_type, customer_id,
                          description=None):
        request = {
            PARAM_APPLICATION_ID: application_id,
            PARAM_TYPE: application_type,
            PARAM_CUSTOMER_ID: customer_id,
            PARAM_DESCRIPTION: description
        }

        request = {k: v for k, v in request.items() if v is not None}
        return self.__make_request(resource=API_APPLICATION, method=HTTP_PATCH,
                                   payload=request)

    def application_delete(self, application_id):
        request = {
            PARAM_APPLICATION_ID: application_id
        }

        return self.__make_request(resource=API_APPLICATION,
                                   method=HTTP_DELETE,
                                   payload=request)

    def parent_get(self, parent_id=None, application_id=None):
        request = {}
        if parent_id:
            request[PARAM_PARENT_ID] = parent_id
        elif application_id:
            request[PARAM_APPLICATION_ID] = application_id
        return self.__make_request(resource=API_PARENT, method=HTTP_GET,
                                   payload=request)

    def parent_post(self, application_id, customer, parent_type,
                    description=None):
        request = {
            PARAM_APPLICATION_ID: application_id,
            PARAM_CUSTOMER_ID: customer,
            PARAM_TYPE: parent_type
        }
        if description:
            request[PARAM_DESCRIPTION] = description
        return self.__make_request(resource=API_PARENT, method=HTTP_POST,
                                   payload=request)

    def parent_patch(self, parent_id, application_id=None, parent_type=None,
                     description=None):
        request = {
            PARAM_PARENT_ID: parent_id,
            PARAM_APPLICATION_ID: application_id,
            PARAM_TYPE: parent_type,
            PARAM_DESCRIPTION: description
        }
        request = {k: v for k, v in request.items() if v is not None}

        return self.__make_request(resource=API_PARENT, method=HTTP_PATCH,
                                   payload=request)

    def parent_delete(self, parent_id):
        request = {
            PARAM_PARENT_ID: parent_id
        }

        return self.__make_request(resource=API_PARENT,
                                   method=HTTP_DELETE,
                                   payload=request)

    def tenant_get(self, tenant_name=None):
        request = {}
        if tenant_name:
            request[PARAM_TENANT_NAME] = tenant_name
        return self.__make_request(resource=API_TENANT, method=HTTP_GET,
                                   payload=request)

    def tenant_post(self, tenant_name, display_name, customer, cloud,
                    read_only=False):
        request = {
            PARAM_NAME: tenant_name,
            PARAM_DISPLAY_NAME: display_name,
            PARAM_TENANT_CUSTOMER: customer,
            PARAM_CLOUD: cloud,
            PARAM_READ_ONLY: read_only
        }
        return self.__make_request(resource=API_TENANT, method=HTTP_POST,
                                   payload=request)

    def tenant_delete(self, tenant_name):
        request = {
            PARAM_NAME: tenant_name
        }
        return self.__make_request(resource=API_TENANT, method=HTTP_DELETE,
                                   payload=request)

    def region_get(self, maestro_name=None):
        request = {}
        if maestro_name:
            request[PARAM_MAESTRO_NAME] = maestro_name
        return self.__make_request(resource=API_REGION, method=HTTP_GET,
                                   payload=request)

    def region_post(self, maestro_name, native_name, cloud, region_id=None):
        request = {
            PARAM_MAESTRO_NAME: maestro_name,
            PARAM_NATIVE_NAME: native_name,
            PARAM_CLOUD: cloud
        }
        if region_id:
            request[PARAM_REGION_ID] = region_id
        return self.__make_request(resource=API_REGION, method=HTTP_POST,
                                   payload=request)

    def region_delete(self, maestro_name):
        request = {
            PARAM_MAESTRO_NAME: maestro_name
        }
        return self.__make_request(resource=API_REGION, method=HTTP_DELETE,
                                   payload=request)

    def tenant_region_get(self, tenant_name):
        request = {
            PARAM_TENANT: tenant_name
        }
        return self.__make_request(resource=API_TENANT_REGION, method=HTTP_GET,
                                   payload=request)


    def tenant_region_post(self, tenant_name, region_name):
        request = {
            PARAM_TENANT: tenant_name,
            PARAM_REGION: region_name
        }
        return self.__make_request(resource=API_TENANT_REGION, method=HTTP_POST,
                                   payload=request)

    def tenant_region_delete(self, tenant_name, region_name):
        request = {
            PARAM_TENANT: tenant_name,
            PARAM_REGION: region_name
        }
        return self.__make_request(resource=API_TENANT_REGION,
                                   method=HTTP_DELETE,
                                   payload=request)

    @staticmethod
    def __read_json(file_path):
        try:
            with open(file_path, 'r') as file:
                content = json.loads(file.read())
        except json.decoder.JSONDecodeError:
            return {'message': 'Invalid file content'}
        if not isinstance(content, list):
            return {'message': 'Invalid file content'}
        return content
