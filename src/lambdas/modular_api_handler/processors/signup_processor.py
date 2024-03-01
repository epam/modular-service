from http import HTTPStatus

from routes.route import Route

from commons.constants import (
    Endpoint,
    HTTPMethod,
)
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.rbac.access_control_service import AccessControlService
from services.user_service import CognitoUserService
from validators.request import SignUpPost
from validators.utils import validate_kwargs
from validators.response import MessageModel

_LOG = get_logger(__name__)


class SignUpProcessor(AbstractCommandProcessor):
    def __init__(self, user_service: CognitoUserService,
                 access_control_service: AccessControlService):
        self.user_service = user_service
        self.access_control_service = access_control_service

    @classmethod
    def build(cls) -> 'SignUpProcessor':
        return cls(
            user_service=SERVICE_PROVIDER.user_service,
            access_control_service=SERVICE_PROVIDER.access_control_service,
        )

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.SIGNUP,
                HTTPMethod.POST,
                'post',
                response=(HTTPStatus.OK, MessageModel, None),
                require_auth=False,
                permission=None
            ),
        )

    @validate_kwargs
    def post(self, event: SignUpPost):
        role = event.role
        if not self.access_control_service.role_exists(role):
            _LOG.warning(f'Invalid role name: {role}')
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'Invalid role name: {role}'
            ).exc()
        _LOG.debug(f'Role \'{role}\' exists')
        self.user_service.save(
            username=event.username,
            password=event.password,
            role=role
        )
        _LOG.debug(f'Saving user: {event.username}')
        return build_response(content=f'The user {event.username} was created')
