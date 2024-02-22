
from http import HTTPStatus

from routes.route import Route

from commons.constants import Endpoint, HTTPMethod, PASSWORD_ATTR, USERNAME_ATTR
from commons.lambda_response import ResponseFactory
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.user_service import CognitoUserService

_LOG = get_logger(__name__)


class SignInProcessor(AbstractCommandProcessor):
    def __init__(self, user_service: CognitoUserService):
        self.user_service = user_service

    @classmethod
    def build(cls) -> 'SignInProcessor':
        return cls(
            user_service=SERVICE_PROVIDER.user_service,
        )

    @classmethod
    def routes(cls) -> list[Route]:
        name = cls.controller_name()
        return [
            Route(None, Endpoint.SIGNIN.value, controller=name, action='post',
                  conditions={'method': [HTTPMethod.POST]}),
        ]

    def post(self, event):
        _LOG.debug(f'Sign in event: {event}')
        username = event.get(USERNAME_ATTR)
        password = event.get(PASSWORD_ATTR)
        if not username or not password:
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                'You must specify both username and password'
            ).exc()

        _LOG.debug('Going to initiate the authentication flow')
        auth_result = self.user_service.initiate_auth(
            username=username,
            password=password)
        if not auth_result:
            raise ResponseFactory(HTTPStatus.UNAUTHORIZED).message(
                'Incorrect username or password'
            ).exc()

        # _state = "contains" if auth_result.get(
        #     "ChallengeName") else "does not contain"
        # _LOG.debug(f'Authentication initiation response '
        #            f'{_state} the challenge')
        #
        # if auth_result.get('ChallengeName'):
        #     _LOG.debug(f'Responding to an authentication challenge '
        #                f'{auth_result.get("ChallengeName")} ')
        #     auth_result = self.user_service.respond_to_auth_challenge(
        #         challenge_name=auth_result['ChallengeName'])
        refresh_token = auth_result['AuthenticationResult']['RefreshToken']
        id_token = auth_result['AuthenticationResult']['IdToken']

        return ResponseFactory().raw({
            'access_token': id_token,
            # 'refresh_token': refresh_token
        }).build()
