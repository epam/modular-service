import inspect
import json
import re
from http import HTTPStatus
from typing import Callable

from bottle import Bottle, HTTPResponse, request

from commons import RequestContext
from commons.lambda_response import ApplicationException, LambdaResponse, \
    ResponseFactory
from commons.constants import HTTPMethod, Endpoint
from commons.log_helper import get_logger
from lambdas.modular_api_handler.handler import lambda_handler
from services import SERVICE_PROVIDER

_LOG = get_logger(__name__)


class AuthPlugin:
    """
    Authenticates the user
    """

    def __init__(self):
        self.name = 'auth'

    @staticmethod
    def get_token_from_header(header: str) -> str | None:
        """
        Retrieves bearer token from http header value
        """
        if not header or not isinstance(header, str):
            return
        parts = header.split()
        if len(parts) == 1:
            return parts[0]
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]

    @staticmethod
    def _to_bottle_resp(resp: LambdaResponse) -> HTTPResponse:
        built = resp.build()
        return HTTPResponse(
            body=built['body'],
            status=built['statusCode'],
            headers=built['headers']
        )

    def __call__(self, callback: Callable):
        def wrapper(*args, **kwargs):
            header = (request.headers.get('Authorization') or
                      request.headers.get('authorization'))
            token = self.get_token_from_header(header)

            if not token:
                resp = ResponseFactory(HTTPStatus.UNAUTHORIZED).default()
                return self._to_bottle_resp(resp)

            try:
                decoded = SERVICE_PROVIDER.cognito.decode_token(token)
            except ApplicationException as e:
                return self._to_bottle_resp(e.response)

            sign = inspect.signature(callback)
            if 'decoded_token' in sign.parameters:
                _LOG.debug('Expanding callback with decoded token')
                kwargs['decoded_token'] = decoded
            return callback(*args, **kwargs)

        return wrapper


class OnPremApiBuilder:
    dynamic_resource_regex = re.compile(r'([^{/]+)(?=})')
    without_auth = {
        (HTTPMethod.POST, Endpoint.SIGNIN),
        (HTTPMethod.POST, Endpoint.SIGNUP)
    }

    @staticmethod
    def _register_errors(app: Bottle) -> None:
        @app.error(404)
        def not_found(error):
            return json.dumps({'message': HTTPStatus.NOT_FOUND.phrase},
                              separators=(',', ':'))

        @app.error(500)
        def not_found(error):
            return json.dumps(
                {'message': HTTPStatus.INTERNAL_SERVER_ERROR.phrase},
                separators=(',', ':')
            )

    def build(self, prefix: str = 'dev') -> Bottle:
        """
        Builds on-prem bottle application that includes:
        - custom auth plugin
        - custom handlers for 404 and 500 errors
        - one callback that proxies everything to a single available
          lambda. Bottle resolver is not used because we also need that
          lambda to be able to response requests from API Gateway, so
          dispatcher is inside lambda.
        :param prefix: url stage for all the endpoints,
        (from deployment_resources)
        :type prefix: str
        """
        app = Bottle()
        self._register_errors(app)

        prefix_app = Bottle()

        # exception currently hardcoded in order not to bring
        # deployment resources here
        for method, path in self.without_auth:
            prefix_app.route(
                path=path.value,
                method=method.value,
                callback=self._callback
            )
        # all other requests proxy to lambda but with auth
        prefix_app.route(
            path='<path:path>',
            method=[HTTPMethod.GET, HTTPMethod.POST, HTTPMethod.PATCH,
                    HTTPMethod.DELETE, HTTPMethod.PUT],
            callback=self._callback,
            apply=[AuthPlugin()]

        )
        app.mount(prefix.strip('/'), prefix_app)
        return app

    @staticmethod
    def _callback(decoded_token: dict | None = None, **path_params):
        method = request.method
        path = request.route.rule
        event = {
            'httpMethod': request.method,
            'path': request.path,
            'headers': dict(request.headers),
            'requestContext': {
                # 'stage': '',  # currently, not used on onprem
                'resourcePath': path.replace('<', '{').replace('>', '}').replace('proxy', 'proxy+'),  # kludge
                'path': request.fullpath
            },
            'pathParameters': path_params
        }
        if decoded_token:
            event['requestContext']['authorizer'] = {
                'claims': {
                    'cognito:username': decoded_token.get('cognito:username'),
                    'sub': decoded_token.get('sub'),
                    'custom:customer': decoded_token.get('custom:customer'),
                    'custom:is_system': decoded_token.get('custom:is_system'),
                    'custom:role': decoded_token.get('custom:role'),
                }
            }

        if method == 'GET':
            event['queryStringParameters'] = dict(request.query)
        else:
            event['body'] = request.body.read().decode()
            event['isBase64Encoded'] = False

        response = lambda_handler(event, RequestContext())

        return HTTPResponse(
            body=response['body'],
            status=response['statusCode'],
            headers=response['headers']
        )
