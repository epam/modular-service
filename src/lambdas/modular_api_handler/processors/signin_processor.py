from http import HTTPStatus

from routes.route import Route

from commons.constants import Endpoint, HTTPMethod
from commons.lambda_response import ResponseFactory
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.user_service import CognitoUserService
from validators.request import SignInPost
from validators.utils import validate_kwargs
from validators.response import SignInResponse

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
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.SIGNIN,
                HTTPMethod.POST,
                'post',
                response=(HTTPStatus.OK, SignInResponse, 'Successful login'),
                require_auth=False,
                permission=None
            ),
        )

    @validate_kwargs
    def post(self, event: SignInPost):
        _LOG.debug('Going to initiate the authentication flow')
        auth_result = self.user_service.initiate_auth(
            username=event.username,
            password=event.password
        )
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
