from http import HTTPStatus
from typing import TYPE_CHECKING

from routes.route import Route
from urllib3.util import parse_url, Url

from commons import urljoin
from commons.__version__ import __version__
from commons.abstract_lambda import ProcessedEvent
from commons.constants import Endpoint, HTTPMethod
from commons.lambda_response import LambdaResponse, ResponseFactory
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SP
from services.openapi_spec_generator import OpenApiGenerator

if TYPE_CHECKING:
    from services.environment_service import EnvironmentService

_LOG = get_logger(__name__)

SWAGGER_HTML = \
"""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="SwaggerUI" />
    <title>SwaggerUI</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@{version}/swagger-ui.css" />
  </head>
  <body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@{version}/swagger-ui-bundle.js" crossorigin></script>
  <script src="https://unpkg.com/swagger-ui-dist@{version}/swagger-ui-standalone-preset.js" crossorigin></script>
  <script>
    window.onload = () => {{
      window.ui = SwaggerUIBundle({{
        url: '{url}',
        dom_id: '#swagger-ui',
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        layout: "StandaloneLayout",
      }});
    }};
  </script>
  </body>
</html>
"""


class SwaggerProcessor(AbstractCommandProcessor):
    def __init__(self, environment_service: 'EnvironmentService'):
        self._env = environment_service

    @classmethod
    def build(cls) -> 'SwaggerProcessor':
        return cls(environment_service=SP.environment_service)

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.DOC,
                HTTPMethod.GET,
                'get',
                response=[(HTTPStatus.OK, None, None)],
                require_auth=False,
                permission=None
            ),
            cls.route(
                Endpoint.DOC_SWAGGER_JSON,
                HTTPMethod.GET,
                'get_spec',
                response=[(HTTPStatus.OK, None, None)],
                require_auth=False,
                permission=None
            ),
        )

    @staticmethod
    def _resolve_urls(headers: dict) -> list[str]:
        scheme = headers.get('X-Forwarded-Proto')
        host = headers.get('Host')
        if scheme:
            return [f'{scheme.lower()}://{host}']
        parsed: Url = parse_url(host)
        port = parsed.port or 443
        scheme = parsed.scheme or ('https' if port == 443 else 'http')
        return [f'{scheme}://{host}']

    @staticmethod
    def _resolve_stage(event: ProcessedEvent) -> str:
        original = event['headers'].get('X-Original-Uri')
        if original:  # nginx reverse proxy gives this header
            # event['path'] here contains full path without stage
            return original[:-len(event['path'])].strip('/')
        # we could've got stage from requestContext.stage, but it always points
        # to api gw stage. That value if wrong for us in case we use a domain
        # name with prefix. So we should resolve stage as difference between
        # requestContext.path and requestContext.resourcePath
        _path = event['fullpath']
        _resource = event['resource']
        return _path[:-len(_resource)].strip('/')

    def get(self, event: dict, _pe: ProcessedEvent):
        out = SWAGGER_HTML.format(
            version='latest',  # get from env?
            url=urljoin(
                '/',
                self._resolve_stage(_pe),
                Endpoint.DOC_SWAGGER_JSON.value
            )
        )
        return LambdaResponse(
            code=HTTPStatus.OK,
            content=out,
            headers={'Content-Type': 'text/html'}
        ).build()

    def get_spec(self, event: dict, _pe: ProcessedEvent):
        from lambdas.modular_api_handler.handler import HANDLER
        _LOG.debug('Returning openapi spec')
        spec = OpenApiGenerator(
            title='Modular service API',
            description='Modular service rest API',
            url=self._resolve_urls(_pe['headers']),
            stages=self._resolve_stage(_pe),
            version=__version__,
            endpoints=HANDLER.iter_endpoint()
        ).generate()
        _LOG.debug('Open api spec was generated')
        return ResponseFactory().raw(spec).build()
