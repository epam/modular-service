from http import HTTPStatus

from routes.route import Route

from commons.constants import Endpoint, HTTPMethod
from commons.lambda_response import build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from validators.request import BaseModel
from validators.utils import validate_kwargs

_LOG = get_logger(__name__)


class HealthCheckProcessor(AbstractCommandProcessor):
    @classmethod
    def build(cls) -> 'HealthCheckProcessor':
        return cls()

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.HEALTH_LIVE,
                HTTPMethod.GET,
                'get',
                response=(HTTPStatus.OK, None, None),
                permission=None,
                require_auth=False
            ),
        )

    @validate_kwargs
    def get(self, event: BaseModel):
        return build_response()
