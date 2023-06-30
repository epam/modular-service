from typing import List

from routes.route import Route

from commons import RESPONSE_BAD_REQUEST_CODE, build_response, RESPONSE_OK_CODE
from commons.constants import POST_METHOD, USERNAME_ATTR, PASSWORD_ATTR, \
    ROLE_ATTR
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import \
    AbstractCommandProcessor
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
            user_service=SERVICE_PROVIDER.user_service(),
            access_control_service=SERVICE_PROVIDER.access_control_service()
        )

    @classmethod
    def routes(cls) -> List[Route]:
        name = cls.controller_name()
        return [
            Route(None, '/signup', controller=name, action='post',
                  conditions={'method': [POST_METHOD]}),
        ]

    def post(self, event):
        _LOG.debug(f'Sign up event: {event}')
        username = event.get(USERNAME_ATTR)
        password = event.get(PASSWORD_ATTR)
        role = event.get(ROLE_ATTR)
        if not all([username, password, role]):
            _LOG.error('You must specify all required parameters: username, '
                       'password, customer, role.')
            raise build_response(
                code=RESPONSE_BAD_REQUEST_CODE,
                content='You must specify all required parameters: username, '
                        'password, customer, role.')

        if not self.access_control_service.role_exists(role):
            _LOG.error(f'Invalid role name: {role}')
            raise build_response(
                code=RESPONSE_BAD_REQUEST_CODE,
                content=f'Invalid role name: {role}')
        _LOG.debug(f'Role \'{role}\' exists')
        self.user_service.save(username=username, password=password, role=role)
        _LOG.debug(f'Saving user: {username}')
        return build_response(
            code=RESPONSE_OK_CODE,
            content=f'The user {username} was created')
