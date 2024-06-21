from http import HTTPStatus
from typing import cast

from routes.route import Route

from commons.abstract_lambda import ProcessedEvent
from commons.constants import Endpoint, HTTPMethod, Permission
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.user_service import CognitoUserService
from validators.request import RefreshPostModel, SignInPost, UserResetPasswordModel
from validators.response import SignInResponse
from validators.utils import validate_kwargs

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
            cls.route(
                Endpoint.REFRESH,
                HTTPMethod.POST,
                'refresh',
                response=(HTTPStatus.OK, SignInResponse, 'Successful token refresh'),
                require_auth=False,
                permission=None
            ),
            cls.route(
                Endpoint.USERS_RESET_PASSWORD,
                HTTPMethod.POST,
                'reset_password',
                response=(HTTPStatus.NO_CONTENT, None, 'Successfully changed'),
                require_auth=True,
                permission=Permission.USERS_RESET_PASSWORD
            )
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

        return ResponseFactory().raw({
            'access_token': auth_result['id_token'],
            'refresh_token': auth_result['refresh_token'],
            'expires_in': auth_result['expires_in']
        }).build()

    @validate_kwargs
    def refresh(self, event: RefreshPostModel):
        _LOG.debug('Going to initiate refresh flow')
        res = self.user_service.refresh_token(event.refresh_token)
        if not res:
            raise ResponseFactory(HTTPStatus.UNAUTHORIZED).default().exc()

        return ResponseFactory().raw({
            'access_token': res['id_token'],
            'refresh_token': res['refresh_token'],
            'expires_in': res['expires_in']
        }).build()

    @validate_kwargs
    def reset_password(self, event: UserResetPasswordModel,
                       _pe: ProcessedEvent):
        username = cast(str, _pe['cognito_username'])
        self.user_service.set_password(username, event.new_password)
        return build_response(code=HTTPStatus.NO_CONTENT)
