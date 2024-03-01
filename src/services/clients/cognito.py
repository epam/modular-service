from abc import ABC, abstractmethod
from functools import cached_property
from http import HTTPStatus
from typing import Generator

import boto3

from commons.lambda_response import ResponseFactory
from commons.log_helper import get_logger
from services.environment_service import EnvironmentService

_LOG = get_logger(__name__)
CUSTOM_ROLE_ATTR = 'custom:modular_role'
CUSTOM_CUSTOMER = 'custom:customer'
CUSTOM_IS_SYSTEM = 'custom:is_system'


class BaseAuthClient(ABC):
    @abstractmethod
    def admin_initiate_auth(self, username: str, password: str) -> dict | None:
        ...

    @abstractmethod
    def sign_up(self, username: str, password: str, role: str | None = None,
                customer: str | None = None, is_system: bool = False):
        ...

    @abstractmethod
    def set_password(self, username: str, password: str,
                     permanent: bool = True):
        ...

    @abstractmethod
    def is_user_exists(self, username: str) -> bool:
        ...


class CognitoClient(BaseAuthClient):
    def __init__(self, environment_service: EnvironmentService):
        self._environment = environment_service

    @cached_property
    def client(self):
        return boto3.client('cognito-idp')

    @cached_property
    def user_pool_id(self) -> str:
        _LOG.info('Retrieving user pool id')
        _id = self._environment.user_pool_id()
        if _id := self._environment.user_pool_id():
            return _id
        resp = ResponseFactory(HTTPStatus.SERVICE_UNAVAILABLE).default()
        name = self._environment.user_pool_name()
        if not name:
            _LOG.error('Cognito pool name|id not found in envs')
            raise resp.exc()
        _id = self._pool_id_from_name(name)
        if not _id:
            _LOG.error(f'Pool by name {name} not found')
            raise resp.exc()
        return _id

    @property
    def client_id(self) -> str:
        client = self.client.list_user_pool_clients(
            UserPoolId=self.user_pool_id, MaxResults=1)['UserPoolClients']
        if not client:
            _message = 'Application Authentication Service is not ' \
                       'configured properly: no client applications found'
            _LOG.error(_message)
            raise ResponseFactory(HTTPStatus.SERVICE_UNAVAILABLE).message(
                _message
            ).exc()
        return client[0]['ClientId']

    def _pool_id_from_name(self, name: str) -> str | None:
        """
        Since AWS Cognito can have two different pools with equal names,
        this method returns the first pool id which will be found.
        """
        for pool in self._list_user_pools():
            if pool['Name'] == name:
                return pool['Id']

    def _list_user_pools(self) -> Generator[dict, None, None]:
        first = True
        params = dict(MaxResults=10)
        while params.get('NextToken') or first:
            pools = self.client.list_user_pools(**params)
            yield from pools.get('UserPools') or []
            params['NextToken'] = pools.get('NextToken')
            if first:
                first = False

    def admin_initiate_auth(self, username: str, password: str) -> dict | None:
        """
        Initiates the authentication flow. Returns AuthenticationResult if
        the caller does not need to pass another challenge. If the caller
        does need to pass another challenge before it gets tokens,
        ChallengeName, ChallengeParameters, and Session are returned.
        """
        try:
            result = self.client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            return result
        except self.client.exceptions.UserNotFoundException:
            return
        except self.client.exceptions.NotAuthorizedException:
            return

    def sign_up(self, username: str, password: str, role: str | None = None,
                customer: str | None = None, is_system: bool = False):
        custom_attr = [{
            'Name': 'name',
            'Value': username
        }]
        if role:
            custom_attr.append({
                'Name': CUSTOM_ROLE_ATTR,
                'Value': role
            })
        if customer:
            custom_attr.append({
                'Name': CUSTOM_CUSTOMER,
                'Value': customer
            })
        if isinstance(is_system, bool):
            custom_attr.append({
                'Name': CUSTOM_IS_SYSTEM,
                'Value': is_system
            })
        validation_data = [
            {
                'Name': 'name',
                'Value': username
            }
        ]
        return self.client.sign_up(ClientId=self.client_id,
                                   Username=username,
                                   Password=password,
                                   UserAttributes=custom_attr,
                                   ValidationData=validation_data)

    def set_password(self, username: str, password: str, permanent=True):
        return self.client.admin_set_user_password(
            UserPoolId=self.user_pool_id,
            Username=username,
            Password=password,
            Permanent=permanent
        )

    def get_user_pool(self, user_pool_name):
        for pool in self._list_user_pools():
            if pool.get('Name') == user_pool_name:
                return pool['Id']

    def _get_user(self, username) -> dict | None:
        users = self.client.list_users(
            UserPoolId=self.user_pool_id,
            Limit=1,
            Filter=f'username = "{username}"')['Users']
        if len(users) >= 1:
            return users[0]

    def is_user_exists(self, username: str) -> bool:
        return not not self._get_user(username)
