from datetime import timedelta
from http import HTTPStatus
import json
import os
import secrets
from typing import TYPE_CHECKING, cast

import bcrypt
from jwcrypto import jwt
from pymongo import MongoClient

from commons.constants import Env, PRIVATE_KEY_SECRET_NAME
from commons.lambda_response import ResponseFactory
from commons.log_helper import get_logger
from models import MONGO_CLIENT
from models.user import User
from services.clients.cognito import AuthenticationResult, BaseAuthClient
from services.clients.jwt_management_client import JWTManagementClient

if TYPE_CHECKING:
    from modular_sdk.services.ssm_service import AbstractSSMClient


_LOG = get_logger(__name__)

EXPIRATION_IN_MINUTES = 60

TOKEN_EXPIRED_MESSAGE = 'The incoming token has expired'


class MongoAndSSMAuthClient(BaseAuthClient):
    def __init__(self, ssm_client: 'AbstractSSMClient'):
        self._ssm = ssm_client
        self._jwt_client = None
        self._refresh_col = cast(MongoClient, MONGO_CLIENT).get_database(
            os.getenv(Env.MONGO_DATABASE)
        ).get_collection('ModularRefreshTokenChains')

    @property
    def jwt_client(self) -> JWTManagementClient:
        if self._jwt_client:
            return self._jwt_client
        jwk_pem = self._ssm.get_parameter(PRIVATE_KEY_SECRET_NAME)
        unavailable = ResponseFactory(HTTPStatus.SERVICE_UNAVAILABLE).default()

        if not jwk_pem or not isinstance(jwk_pem, str):
            _LOG.error('Can not find jwt-secret')
            raise unavailable.exc()
        try:
            cl = JWTManagementClient.from_b64_pem(jwk_pem)
            self._jwt_client = cl
            return cl
        except ValueError:
            raise unavailable.exc()

    def decode_token(self, token: str) -> dict:
        try:
            verified = self.jwt_client.verify(token)
        except jwt.JWTExpired:
            raise ResponseFactory(HTTPStatus.UNAUTHORIZED).message(
                TOKEN_EXPIRED_MESSAGE).exc()
        except (jwt.JWException, ValueError, Exception):
            raise ResponseFactory(HTTPStatus.UNAUTHORIZED).default().exc()
        return json.loads(verified.claims)

    @staticmethod
    def _gen_refresh_token_version() -> str:
        return secrets.token_hex()

    def _gen_refresh_token(self, username: str, version: str) -> str:
        t = self.jwt_client.sign({'username': username, 'version': version})
        return self.jwt_client.encrypt(t)

    def _decrypt_refresh_token(self, token: str) -> tuple[str, str] | None:
        t = self.jwt_client.decrypt(token)
        if not t:
            return
        try:
            t = self.jwt_client.verify(t.claims)
        except Exception:
            return
        dct = json.loads(t.claims)
        return dct['username'], dct['version']

    def _gen_access_token(self, user: User) -> str:
        return self.jwt_client.sign(
            claims={
                'cognito:username': user.user_id,
                'sub': str(user.mongo_id),
                'custom:customer': user.customer,
                'custom:role': user.role,
                'custom:is_system': user.is_system
            },
            exp=timedelta(minutes=EXPIRATION_IN_MINUTES)
        )

    def admin_initiate_auth(self, username: str, password: str
                            ) -> AuthenticationResult | None:

        user_item = User.get_nullable(hash_key=username)
        if not user_item or bcrypt.hashpw(
                password.encode(), user_item.password) != user_item.password:
            return

        rt_version = self._gen_refresh_token_version()
        self._refresh_col.replace_one({'_id': username}, {
            'v': rt_version  # latest version for user
        }, upsert=True)

        return {
            'id_token': self._gen_access_token(user_item),
            'refresh_token': self._gen_refresh_token(username, rt_version),
            'expires_in': EXPIRATION_IN_MINUTES * 60
        }

    def admin_refresh_token(self, refresh_token: str
                            ) -> AuthenticationResult | None:
        _LOG.info('Starting on-prem refresh token flow')
        tpl = self._decrypt_refresh_token(refresh_token)
        if not tpl:
            _LOG.info('Invalid refresh token provided. Cannot refresh')
            return
        username, rt_version = tpl
        latest = self._refresh_col.find_one({'_id': username})
        if not latest or not latest.get('v'):
            _LOG.warning('Latest version of token not found in DB '
                         'but valid token was received. Cannot refresh')
            return
        correct_version = latest['v']
        if rt_version != correct_version:
            _LOG.warning('Valid token received but its version and one from '
                         'DB do not match. Stolen refresh token or user '
                         'reused one. Invalidating existing version')
            self._refresh_col.delete_one({'_id': username})
            return
        rt_version = self._gen_refresh_token_version()
        self._refresh_col.replace_one({'_id': username}, {
            'v': rt_version  # latest version for user
        }, upsert=True)

        user_item = User.get_nullable(hash_key=username)
        return {
            'id_token': self._gen_access_token(user_item),
            'refresh_token': self._gen_refresh_token(username, rt_version),
            'expires_in': EXPIRATION_IN_MINUTES * 60
        }

    @staticmethod
    def _set_password(user: User, password: str):
        user.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def sign_up(self, username: str, password: str, role: str | None = None,
                customer: str | None = None, is_system: bool = False):
        user = User(
            user_id=username,
            customer=customer,
            role=role,
            is_system=is_system
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
