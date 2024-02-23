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

    def save(self, username, password, role):
        _LOG.debug(f'Validating password for user {username}')
        # TODO move to pydantic
        errors = self.__validate_password(password)
        if errors:
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                '; '.join(errors)
            ).exc()
        if self.client.is_user_exists(username):
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'The user with name {username} already exists.'
            ).exc()

        _LOG.debug(f'Creating the user with username {username}')
        self.client.sign_up(username=username, password=password, role=role)
        _LOG.debug(f'Setting the password for the user {username}')
        self.client.set_password(username=username,
                                 password=password)

    def get_user_role_name(self, user: str):
        return self.client.get_user_role(user)

    @staticmethod
    def __validate_password(password):
        errors = []
        upper = any(char.isupper() for char in password)
        numeric = any(char.isdigit() for char in password)
        symbol = any(not char.isalnum() for char in password)
        if not upper:
            errors.append('Password must have uppercase characters')
        if not numeric:
            errors.append('Password must have numeric characters')
        if not symbol:
            errors.append('Password must have symbol characters')
        if len(password) < 8:
            errors.append(f'Invalid length. Valid min length: 8')

        if errors:
            return errors

    def initiate_auth(self, username, password):
        return self.client.admin_initiate_auth(username=username,
                                               password=password)
