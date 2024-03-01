import json
from datetime import timedelta
from http import HTTPStatus
from typing import Any, TYPE_CHECKING

import bcrypt
from jwcrypto import jwt

from commons.constants import PRIVATE_KEY_SECRET_NAME
from commons.lambda_response import ResponseFactory
from commons.log_helper import get_logger
from models.user import User
from services.clients.cognito import BaseAuthClient
from services.clients.jwt_management_client import JWTManagementClient

if TYPE_CHECKING:
    from modular_sdk.services.ssm_service import AbstractSSMClient


_LOG = get_logger(__name__)

EXPIRATION_IN_MINUTES = 60

TOKEN_EXPIRED_MESSAGE = 'The incoming token has expired'


class MongoAndSSMAuthClient(BaseAuthClient):
    def __init__(self, ssm_client: 'AbstractSSMClient'):
        self._ssm = ssm_client

    def _get_jwt_secret(self) -> JWTManagementClient:
        jwk_pem = self._ssm.get_parameter(PRIVATE_KEY_SECRET_NAME)
        unavailable = ResponseFactory(HTTPStatus.SERVICE_UNAVAILABLE).default()

        if not jwk_pem or not isinstance(jwk_pem, str):
            _LOG.error('Can not find jwt-secret')
            raise unavailable.exc()
        try:
            return JWTManagementClient.from_b64_pem(jwk_pem)
        except ValueError:
            raise unavailable.exc()

    def decode_token(self, token: str) -> dict:
        client = self._get_jwt_secret()
        try:
            verified = client.verify(token)
        except jwt.JWTExpired:
            raise ResponseFactory(HTTPStatus.UNAUTHORIZED).message(
                TOKEN_EXPIRED_MESSAGE).exc()
        except (jwt.JWException, ValueError, Exception):
            raise ResponseFactory(HTTPStatus.UNAUTHORIZED).default().exc()
        return json.loads(verified.claims)

    def admin_initiate_auth(self, username: str, password: str) -> dict | None:

        user_item = User.get_nullable(hash_key=username)
        if not user_item or bcrypt.hashpw(
                password.encode(), user_item.password) != user_item.password:
            return

        client = self._get_jwt_secret()
        token = client.sign(
            claims={
                'cognito:username': username,
                'sub': str(user_item.mongo_id),
                'custom:customer': user_item.customer,
                'custom:role': user_item.role,
                'custom:is_system': user_item.is_system
            },
            exp=timedelta(minutes=EXPIRATION_IN_MINUTES)
        )
        return {
            'AuthenticationResult': {
                'IdToken': token,
                'RefreshToken': None,
                'ExpiresIn': EXPIRATION_IN_MINUTES * 60
            }
        }

    @staticmethod
    def _set_password(user: User, password: str):
        user.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def sign_up(self, username: str, password: str, role: str,
                customer: str | None = None):
        user = User(
            user_id=username,
            customer=customer,
            role=role,
            is_system=False
        )
        self._set_password(user, password)
        user.save()

    @staticmethod
    def _get_user(username: str) -> User | None:
        return User.get_nullable(hash_key=username)

    def is_user_exists(self, username: str) -> bool:
        return bool(self._get_user(username))

    def set_password(self, username: str, password: str,
                     permanent: bool = True):
        user = User.get_nullable(hash_key=username)
        self._set_password(user, password)
        user.save()
