from functools import partial
from http import HTTPStatus
from http.client import HTTPResponse
import json
from typing import Iterable, cast
import urllib
import urllib.error
from urllib.parse import quote, urlencode
import urllib.request

from modular_service_cli.service.config import AbstractConfig
from modular_service_cli.service.constants import *
from modular_service_cli.service.logger import get_logger
from modular_service_cli.service.utils import catch, sifted, urljoin, JWTToken

_LOG = get_logger(__name__)


class ApiClient:
    """
    Simple JSON API client which is enough to cover our needs
    """
    __slots__ = ('_api_link',)

    def __init__(self, api_link: str):
        """
        :param api_link: pre-built link, can contain some prefix
        """
        self._api_link = api_link

    def build_url(self, path: str, params: dict | None = None,
                  query: dict | None = None) -> str:
        """
        The methods return full built url which can be used to make request
        :param path: some custodian resource.
        :param params: path params
        :param query: dict with query params
        :return:
        """
        _LOG.debug(f'Building url from {path=}, {params=}, {query=}')
        url = path.format(**(params or {}))
        url = quote(urljoin(url))  # to remove /
        if query:
            url += f'?{urlencode(sifted(query))}'
        _LOG.debug(f'Resulting url: {url=}')
        return urljoin(self._api_link, url)

    @staticmethod
    def prepare_request(url: str, method: HTTPMethod, data: dict | None = None
                        ) -> urllib.request.Request:
        """
        Prepares request instance. Url must be built beforehand
        :param url:
        :param method:
        :param data:
        :return:
        """
        _LOG.debug(f'Preparing request: {url=}, {method=}, {data=}')
        if isinstance(data, dict):
            return urllib.request.Request(
                url=url,
                method=method.value,
                data=json.dumps(data, separators=(',', ':')).encode(),
                headers={'Content-Type': 'application/json'}
            )
        return urllib.request.Request(url=url, method=method.value)

    def open_request(self, *args, **kwargs) -> HTTPResponse:
        return urllib.request.urlopen(*args, **kwargs)


class ApiResponse:
    __slots__ = ('method', 'path', 'code', 'data', 'trace_id', 'api_version',
                 'exc')

    def __init__(self, method: HTTPMethod | None = None,
                 path: Endpoint | None = None,
                 code: HTTPStatus | None = None, data: dict | None = None,
                 trace_id: str | None = None, api_version: str | None = None,
                 exc: Exception | None = None):
        self.method = method
        self.path = path
        self.code = code
        self.data = data
        self.trace_id = trace_id
        self.api_version = api_version

        # JsonDecodeError | urllib.error.URLError - don't know how to handle
        # properly
        self.exc = exc

    @property
    def was_sent(self) -> bool:
        """
        Tells whether the request was sent
        :return:
        """
        return self.code is not None

    @classmethod
    def build(cls, content: str | list | dict | Iterable
              ) -> 'ApiResponse':
        body = {}
        if isinstance(content, str):
            body.update({MESSAGE_ATTR: content})
        elif isinstance(content, dict) and content:
            body.update(content)
        elif isinstance(content, list):
            body.update({ITEMS_ATTR: content})
        elif isinstance(content, Iterable):
            body.update(({ITEMS_ATTR: list(content)}))
        return cls(data=body, code=HTTPStatus.OK)

    @property
    def ok(self) -> bool:
        return self.code is not None and 200 <= self.code <= 206


class ModularServiceApiClient:
    __slots__ = '_config', '_client'

    def __init__(self, config: AbstractConfig):
        # api_link and access_token presence is validated before
        self._config = config
        self._client = ApiClient(api_link=config.api_link)

    def add_token(self, rec: urllib.request.Request,
                  header: str = 'Authorization'):
        """
        Adds token to the given request instance. Refreshes the token if needed
        :param header:
        :param rec:
        :return:
        """
        # access token should definitely exist here because we check its
        # presence before creating this class
        at = cast(str, self._config.access_token)
        rt = self._config.refresh_token
        if JWTToken(at).is_expired() and rt:
            _LOG.info('Trying to auto-refresh token')
            resp = self.refresh(rt)
            if resp.ok:
                _LOG.info('Token was refreshed successfully. Updating config')
                at = resp.data.get('access_token')
                rt = resp.data.get('refresh_token')
                dct = {'access_token': at}
                if rt:
                    # if new one. This probably won't happen because Cognito
                    # does not return a new refresh token. But just in case
                    dct['refresh_token'] = rt
                self._config.update(dct)

        rec.add_header(header, at)

    def _open_request(self, request: urllib.request.Request,
                      response: ApiResponse) -> None:
        """
        Sends the given request instance. Fills the response instance with data
        :param request:
        :param response:  will be filled with some response data
        """
        try:
            resp = self._client.open_request(request)
        except urllib.error.HTTPError as e:
            resp = e
        except urllib.error.URLError as e:
            _LOG.exception('Cannot make a request')
            response.exc = e
            return
        response.code = HTTPStatus(resp.getcode())
        if response.code != HTTPStatus.NO_CONTENT:
            data, exc = catch(partial(json.load, resp), json.JSONDecodeError)
            response.data = data
            response.exc = exc

        response.trace_id = resp.headers.get(LAMBDA_INVOCATION_TRACE_ID_HEADER)
        response.api_version = resp.headers.get(SERVER_VERSION_HEADER)
        resp.close()
        return

    def make_request(self, path: Endpoint,
                     method: HTTPMethod | None = None,
                     path_params: dict | None = None,
                     query: dict | None = None,
                     data: dict | None = None) -> ApiResponse:
        """
        High-level request method. Adds token.
        :param path:
        :param method:
        :param path_params:
        :param query:
        :param data:
        :return:
        """
        if not method:
            method = HTTPMethod.POST if data else HTTPMethod.GET
        req = self._client.prepare_request(
            url=self._client.build_url(path.value, path_params, query),
            method=method,
            data=data
        )
        self.add_token(req)
        response = ApiResponse(method=method, path=path)
        self._open_request(req, response)
        return response

    def refresh(self, token: str):
        req = self._client.prepare_request(
            url=self._client.build_url(Endpoint.REFRESH.value),
            method=HTTPMethod.POST,
            data={'refresh_token': token}
        )
        response = ApiResponse(HTTPMethod.POST, Endpoint.REFRESH)
        self._open_request(req, response)
        return response


    def login(self, username: str, password: str):
        req = self._client.prepare_request(
            url=self._client.build_url(Endpoint.SIGNIN.value),
            method=HTTPMethod.POST,
            data={'username': username, 'password': password}
        )
        response = ApiResponse(HTTPMethod.POST, Endpoint.SIGNIN)
        self._open_request(req, response)
        return response

    def get_role(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.ROLES_NAME,
            path_params={'name': name},
            method=HTTPMethod.GET,
            query=sifted(kwargs)
        )

    def query_roles(self, **kwargs):
        return self.make_request(
            path=Endpoint.ROLES,
            method=HTTPMethod.GET,
            query=sifted(kwargs)
        )

    def create_role(self, **kwargs):
        return self.make_request(
            path=Endpoint.ROLES,
            method=HTTPMethod.POST,
            data=sifted(kwargs)
        )

    def patch_role(self, name: str, **kwargs):
        return self.make_request(
            path=Endpoint.ROLES_NAME,
            method=HTTPMethod.PATCH,
            path_params={'name': name},
            data=sifted(kwargs)
        )

    def delete_role(self, name: str, **kwargs):
        return self.make_request(
            path=Endpoint.ROLES_NAME,
            method=HTTPMethod.DELETE,
            path_params={'name': name},
            data=sifted(kwargs)
        )

    def get_policy(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.POLICIES_NAME,
            method=HTTPMethod.GET,
            path_params={'name': name},
            query=sifted(kwargs)
        )

    def query_policies(self, **kwargs):
        return self.make_request(
            path=Endpoint.POLICIES,
            method=HTTPMethod.GET,
            query=sifted(kwargs)
        )

    def create_policy(self, **kwargs):
        return self.make_request(
            path=Endpoint.POLICIES,
            method=HTTPMethod.POST,
            data=sifted(kwargs) 
        )

    def patch_policy(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.POLICIES_NAME,
            method=HTTPMethod.PATCH,
            path_params={'name': name},
            data=sifted(kwargs)
        )

    def delete_policy(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.POLICIES_NAME,
            method=HTTPMethod.DELETE,
            path_params={'name': name},
            data=sifted(kwargs)
        )

    def get_customer(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.CUSTOMERS_NAME,
            method=HTTPMethod.GET,
            path_params={'name': name},
            query=sifted(kwargs)
        )

    def query_customer(self, **kwargs):
        return self.make_request(
            path=Endpoint.CUSTOMERS,
            method=HTTPMethod.GET,
            query=sifted(kwargs)
        )

    def create_customer(self, **kwargs):
        return self.make_request(
            path=Endpoint.CUSTOMERS,
            method=HTTPMethod.POST,
            data=sifted(kwargs)
        )

    def patch_customer(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.CUSTOMERS_NAME,
            method=HTTPMethod.PATCH,
            path_params={'name': name},
            data=sifted(kwargs)
        )

    def activate_customer(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.CUSTOMERS_NAME_ACTIVATE,
            method=HTTPMethod.POST,
            path_params={'name': name},
            data=sifted(kwargs)
        )

    def deactivate_customer(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.CUSTOMERS_NAME_DEACTIVATE,
            method=HTTPMethod.POST,
            path_params={'name': name},
            data=sifted(kwargs)
        )

    def get_region(self, name):
        return self.make_request(
            path=Endpoint.REGIONS_NAME,
            method=HTTPMethod.GET,
            path_params={'name': name}
        )

    def query_regions(self, **kwargs):
        return self.make_request(
            path=Endpoint.REGIONS,
            method=HTTPMethod.GET,
            data=sifted(kwargs)
        )

    def create_region(self, **kwargs):
        return self.make_request(
            path=Endpoint.REGIONS,
            method=HTTPMethod.POST,
            data=sifted(kwargs)
        )

    def delete_region(self, name):
        return self.make_request(
            path=Endpoint.REGIONS_NAME,
            method=HTTPMethod.DELETE,
            path_params={'name': name}
        )

    def get_tenant(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.TENANTS_NAME,
            method=HTTPMethod.GET,
            path_params={'name': name},
            query=sifted(kwargs)
        )

    def query_tenants(self, **kwargs):
        return self.make_request(
            path=Endpoint.TENANTS,
            method=HTTPMethod.GET,
            query=sifted(kwargs)
        )

    def create_tenant(self, **kwargs):
        return self.make_request(
            path=Endpoint.TENANTS,
            method=HTTPMethod.POST,
            data=sifted(kwargs)
        )

    def delete_tenant(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.TENANTS_NAME,
            method=HTTPMethod.DELETE,
            path_params={'name': name},
            data=sifted(kwargs)
        )

    def activate_tenant(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.TENANTS_NAME_ACTIVATE,
            method=HTTPMethod.POST,
            path_params={'name': name},
            data=sifted(kwargs)
        )

    def deactivate_tenant(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.TENANTS_NAME_DEACTIVATE,
            method=HTTPMethod.POST,
            path_params={'name': name},
            data=sifted(kwargs)
        )

    def get_tenant_regions(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.TENANTS_NAME_REGIONS,
            method=HTTPMethod.GET,
            path_params={'name': name},
            query=sifted(kwargs)
        )

    def add_tenant_region(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.TENANTS_NAME_REGIONS,
            method=HTTPMethod.POST,
            path_params={'name': name},
            data=sifted(kwargs)
        )

    def delete_tenant_region(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.TENANTS_NAME_REGIONS,
            method=HTTPMethod.DELETE,
            path_params={'name': name},
            data=sifted(kwargs)
        )

    def get_tenant_settings(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.TENANTS_NAME_SETTINGS,
            method=HTTPMethod.GET,
            path_params={'name': name},
            query=sifted(kwargs)
        )

    def put_tenant_settings(self, name, **kwargs):
        return self.make_request(
            path=Endpoint.TENANTS_NAME_SETTINGS,
            method=HTTPMethod.PUT,
            path_params={'name': name},
            query=sifted(kwargs)
        )

    def get_application(self, id, **kwargs):
        return self.make_request(
            path=Endpoint.APPLICATIONS_ID,
            method=HTTPMethod.GET,
            path_params={'id': id},
            query=sifted(kwargs)
        )

    def query_application(self, **kwargs):
        return self.make_request(
            path=Endpoint.APPLICATIONS,
            method=HTTPMethod.GET,
            query=sifted(kwargs)
        )

    def patch_application(self, id, **kwargs):
        return self.make_request(
            path=Endpoint.APPLICATIONS_ID,
            method=HTTPMethod.PATCH,
            path_params={'id': id},
            query=sifted(kwargs)
        )

    def delete_application(self, id, **kwargs):
        return self.make_request(
            path=Endpoint.APPLICATIONS_ID,
            method=HTTPMethod.DELETE,
            path_params={'id': id},
            query=sifted(kwargs)
        )

    def create_application_aws_role(self, **kwargs):
        return self.make_request(
            path=Endpoint.APPLICATIONS_AWS_ROLE,
            method=HTTPMethod.POST,
            data=sifted(kwargs)
        )

    def create_application_aws_credentials(self, **kwargs):
        return self.make_request(
            path=Endpoint.APPLICATIONS_AWS_CREDENTIALS,
            method=HTTPMethod.POST,
            data=sifted(kwargs)
        )

    def create_application_azure_credentials(self, **kwargs):
        return self.make_request(
            path=Endpoint.APPLICATIONS_AZURE_CREDENTIALS,
            method=HTTPMethod.POST,
            data=sifted(kwargs)
        )

    def create_application_azure_certificate(self, **kwargs):
        return self.make_request(
            path=Endpoint.APPLICATIONS_AZURE_CERTIFICATE,
            method=HTTPMethod.POST,
            data=sifted(kwargs)
        )

    def create_application_gcp_service_account(self, **kwargs):
        return self.make_request(
            path=Endpoint.APPLICATIONS_GCP_SERVICE_ACCOUNT,
            method=HTTPMethod.POST,
            data=sifted(kwargs)
        )
