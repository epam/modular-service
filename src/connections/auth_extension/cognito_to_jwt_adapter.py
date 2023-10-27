import json
import time
from datetime import datetime
from typing import Union

import bcrypt
from jwcrypto import jwt, jwk

from commons import ApplicationException, RESPONSE_UNAUTHORIZED, \
    get_iso_timestamp
from commons.log_helper import get_logger
from models.user import User

_LOG = get_logger(__name__)

AUTH_TOKEN_NAME = 'token'
EXPIRATION_IN_MINUTES = 60

WRONG_USER_CREDENTIALS_MESSAGE = 'Incorrect username or password'


class CognitoToJWTAdapter:
    def __init__(self, storage_service):
        self.storage_service = storage_service

    def list_user_pools(self):
        """ Not used in onprem mode"""
        pass

    def admin_initiate_auth(self, username, password):
        # todo implement refresh token

        user_item = User.get_nullable(hash_key=username)
        if not user_item or bcrypt.hashpw(
                password.encode(), user_item.password) != user_item.password:
            _LOG.error(WRONG_USER_CREDENTIALS_MESSAGE)
            raise ApplicationException(
                code=RESPONSE_UNAUTHORIZED,
                content=WRONG_USER_CREDENTIALS_MESSAGE)

        jwt_secret = self.storage_service.get_secret_value(AUTH_TOKEN_NAME)
        if not jwt_secret:
            _LOG.error('Can not find jwtsecret')
            raise ApplicationException(
                code=RESPONSE_UNAUTHORIZED,
                content=WRONG_USER_CREDENTIALS_MESSAGE)
        try:
            jwt_secret = json.loads(str(jwt_secret))
        except json.JSONDecodeError:
            _LOG.error('Invalid jwtsecret format')
            raise ApplicationException(
                code=RESPONSE_UNAUTHORIZED,
                content=WRONG_USER_CREDENTIALS_MESSAGE)
        self.update_latest_login(username)
        jwt_token = jwt.JWT(
            header=jwt_secret['header'],
            claims={'user_id': username, 'customer': user_item.customer,
                    'role': user_item.role,
                    'token_date': str(datetime.now()),
                    'exp': round(time.time()) + EXPIRATION_IN_MINUTES * 60
                    }
        )
        jwk_key = jwk.JWK.from_password(jwt_secret['phrase'])
        jwt_token.make_encrypted_token(jwk_key)
        jwe_token = jwt_token.serialize()
        return {
            'AuthenticationResult': {
                'IdToken': jwe_token, 'RefreshToken': []
            }
        }

    def respond_to_auth_challenge(self, challenge_name, user_pool_id):
        """ Not used in onprem mode"""
        pass

    def sign_up(self, username: str, password: str, customer: str, role: str):
        user = User()
        user.user_id = username
        user.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        user.customer = customer
        user.role = role
        User.save(user)
        return True

    @staticmethod
    def get_user(username):
        user = User.get_nullable(hash_key=username)
        if user:
            return user.user_id
        _LOG.error(f'No user with username {username} was found')
        return None

    @staticmethod
    def is_user_exists(username):
        user = User.get_nullable(hash_key=username)
        return True if user else False

    @staticmethod
    def get_user_role(username):
        user = User.get_nullable(hash_key=username)
        if not user:
            _LOG.error(f'No user with username {username} was found')
            return False
        return user.role if user.role else False

    @staticmethod
    def get_user_customer(username):
        user = User.get_nullable(hash_key=username)
        if not user:
            _LOG.error(f'No user with username {username} was found')
            return False
        return user.customer if user.customer else False

    @staticmethod
    def get_user_latest_login(username):
        user = User.get_nullable(hash_key=username)
        if not user:
            _LOG.error(f'No user with username {username} was found')
            return None
        return user.latest_login if user.latest_login else None

    @staticmethod
    def update_role(username, role):
        user = User.get_nullable(hash_key=username)
        if not user:
            _LOG.error(f'No user with username {username} was found')
            return False
        user.role = role
        user.save()

    @staticmethod
    def update_customer(username, customer):
        user = User.get_nullable(hash_key=username)
        if not user:
            _LOG.error(f'No user with username {username} was found')
            return False
        user.customer = customer
        user.save()

    @staticmethod
    def update_latest_login(username: str,
                            latest_login: Union[str, datetime, None] = None):
        latest_login = latest_login or get_iso_timestamp()
        if isinstance(latest_login, datetime):
            latest_login = latest_login.isoformat()
        user = User.get_nullable(hash_key=username)
        if not user:
            _LOG.error(f'No user with username {username} was found')
            return None
        user.latest_login = latest_login
        user.save()

    @staticmethod
    def delete_role(username):
        user = User.get_nullable(hash_key=username)
        if not user:
            _LOG.error(f'No user with username {username} was found')
            return False
        user.role = None
        user.save()

    @staticmethod
    def delete_customer(username):
        user = User.get_nullable(hash_key=username)
        if not user:
            _LOG.error(f'No user with username {username} was found')
            return False
        user.customer = None
        user.save()

    def set_password(self, username, password, **kwargs):
        """ Not used in onprem mode"""
        pass

    @staticmethod
    def is_system_user_exists() -> bool:
        """Checks whether user with customer='SYSTEM' already exists"""
        scan_results = User.scan(User.customer == 'SYSTEM')
        if not scan_results:
            return False
        number_of_system_users = len(scan_results)
        if number_of_system_users == 0:
            return False
        elif number_of_system_users == 1:
            return True
        elif number_of_system_users > 1:
            raise AssertionError("Only one SYSTEM user must be!")

    @staticmethod
    def get_system_user():
        users = list(User.scan(User.customer == 'SYSTEM'))
        if users:
            return users[0].user_id
        else:
            _LOG.info("No SYSTEM user was found")
            return None

    @staticmethod
    def get_customers_latest_logins(customers=None):
        result = {}
        users = list(User.scan())
        for user in users:
            result[user.customer] = user.latest_login
        if customers:
            result = {k: v for k, v in result.items() if k in customers}
        return result

