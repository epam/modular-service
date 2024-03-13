from http import HTTPStatus
from typing import TYPE_CHECKING

from commons.lambda_response import ResponseFactory
from commons.log_helper import get_logger

if TYPE_CHECKING:
    from services.clients.cognito import BaseAuthClient

_LOG = get_logger(__name__)


class CognitoUserService:

    def __init__(self, client: 'BaseAuthClient'):
        self.client = client

    def save(self, username: str, password: str, role: str | None = None,
             customer: str | None = None, is_system: bool = False):
        if self.client.is_user_exists(username):
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'The user with name {username} already exists.'
            ).exc()

        _LOG.debug(f'Creating the user with username {username}')
        self.client.sign_up(username=username, password=password, role=role,
                            customer=customer, is_system=is_system)
        _LOG.debug(f'Setting the password for the user {username}')
        self.client.set_password(username=username,
                                 password=password)

    def initiate_auth(self, username, password):
        return self.client.admin_initiate_auth(username=username,
                                               password=password)
