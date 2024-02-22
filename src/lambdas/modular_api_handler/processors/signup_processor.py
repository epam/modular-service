
from http import HTTPStatus

from routes.route import Route

from commons.constants import (
    Endpoint,
    HTTPMethod,
    PASSWORD_ATTR,
    ROLE_ATTR,
    USERNAME_ATTR,
)
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.rbac.access_control_service import AccessControlService
from services.user_service import CognitoUserService

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
    def routes(cls) -> list[Route]:
        name = cls.controller_name()
        return [
            Route(None, Endpoint.SIGNUP.value, controller=name, action='post',
                  conditions={'method': [HTTPMethod.POST]}),
        ]

    def post(self, event):
        _LOG.debug(f'Sign up event: {event}')
        username = event.get(USERNAME_ATTR)
        password = event.get(PASSWORD_ATTR)
        role = event.get(ROLE_ATTR)
        if not all((username, password, role)):
            _LOG.warning('You must specify all required parameters: username, '
                         'password, customer, role.')
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                'You must specify all required parameters: username, password, customer, role.'
            ).exc()

        if not self.access_control_service.role_exists(role):
            _LOG.warning(f'Invalid role name: {role}')
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'Invalid role name: {role}'
            ).exc()
        _LOG.debug(f'Role \'{role}\' exists')
        self.user_service.save(username=username, password=password, role=role)
        _LOG.debug(f'Saving user: {username}')
        return build_response(content=f'The user {username} was created')
