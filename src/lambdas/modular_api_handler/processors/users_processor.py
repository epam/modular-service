from http import HTTPStatus
import operator
from typing import cast

from routes.route import Route

from commons import NextToken
from commons.abstract_lambda import ProcessedEvent
from commons.constants import Endpoint, HTTPMethod, Permission
from commons.lambda_response import build_response, ResponseFactory
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SP
from services.clients.cognito import BaseAuthClient, UserWrapper
from services.customer_mutator_service import CustomerMutatorService
from services.rbac_service import RBACService
from validators.request import BaseModel, UserPatchModel, UserPostModel, \
    BasePaginationModel, SignUpPost, SignInPost, RefreshPostModel, UserResetPasswordModel
from validators.response import UserResponse, UsersResponse, MessageModel, SignInResponse
from validators.utils import validate_kwargs

_LOG = get_logger(__name__)


class UsersProcessor(AbstractCommandProcessor):
    def __init__(self, users_client: BaseAuthClient,
                 rbac_service: RBACService,
                 customer_service: CustomerMutatorService):
        self.users_client = users_client
        self.rbac_service = rbac_service
        self._cs = customer_service

    @classmethod
    def build(cls) -> 'UsersProcessor':
        return cls(
            users_client=SP.users_client,
            rbac_service=SP.rbac_service,
            customer_service=SP.customer_service
        )

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.USERS_WHOAMI,
                HTTPMethod.GET,
                'whoami',
                summary='Returns information about the user making the request',
                response=[(HTTPStatus.OK, UserResponse, None)],
                require_auth=True,
                permission=Permission.USERS_GET_CALLER
            ),
            cls.route(
                Endpoint.USERS,
                HTTPMethod.GET,
                'query',
                summary='Query multiple users',
                response=[(HTTPStatus.OK, UsersResponse, None)],
                require_auth=True,
                permission=Permission.USERS_DESCRIBE
            ),
            cls.route(
                Endpoint.USERS,
                HTTPMethod.POST,
                'post',
                summary='Create a new user',
                response=[(HTTPStatus.CREATED, UserResponse, None)],
                require_auth=True,
                permission=Permission.USERS_CREATE
            ),
            cls.route(
                Endpoint.USERS_USERNAME,
                HTTPMethod.GET,
                'get',
                summary='Get a specific user by username',
                response=[(HTTPStatus.OK, UserResponse, None),
                          (HTTPStatus.NOT_FOUND, None, None)],
                require_auth=True,
                permission=Permission.USERS_DESCRIBE
            ),
            cls.route(
                Endpoint.USERS_USERNAME,
                HTTPMethod.PATCH,
                'patch',
                summary='Update attributes of a specific user',
                response=[(HTTPStatus.OK, UserResponse, None),
                          (HTTPStatus.NOT_FOUND, None, None)],
                require_auth=True,
                permission=Permission.USERS_UPDATE
            ),
            cls.route(
                Endpoint.USERS_USERNAME,
                HTTPMethod.DELETE,
                'delete',
                summary='Delete a specific user by username',
                response=[(HTTPStatus.NO_CONTENT, None, None)],
                require_auth=True,
                permission=Permission.USERS_DELETE
            ),
            cls.route(
                Endpoint.SIGNUP,

                HTTPMethod.POST,
                'signup',
                summary='Create a new customer, new user for that customer '
                        'admin policy and role for this user',
                response=[(HTTPStatus.CREATED, MessageModel, None),
                          (HTTPStatus.CONFLICT, MessageModel, None)],
                require_auth=False,
                permission=None
            ),
            cls.route(
                Endpoint.SIGNIN,
                HTTPMethod.POST,
                'signin',
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
    def query(self, event: BasePaginationModel):
        cursor = self.users_client.query_users(
            customer=event.customer_id,
            limit=event.limit,
            next_token=NextToken.from_input(event.next_token).value
        )
        items = list(cursor)
        return ResponseFactory().items(
            it=(i.get_dto() for i in items),
            next_token=NextToken(cursor.next_token)
        ).build()

    @validate_kwargs
    def post(self, event: UserPostModel):
        if self.users_client.does_user_exist(event.username):
            raise ResponseFactory(HTTPStatus.CONFLICT).message(
                f'User with such username already exists'
            ).exc()
        if not self.rbac_service.get_role(event.customer_id, event.role_name):
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'Role {event.role_name} not found in customer '
                f'{event.customer_id}'
            ).exc()

        user = self.users_client.signup_user(
            username=event.username,
            password=event.password,
            customer=event.customer_id,
            role=event.role_name,
            is_system=False
        )
        # seems like we need this additional step for cognito
        self.users_client.set_user_password(event.username, event.password)
        return build_response(user.get_dto())

    @validate_kwargs
    def get(self, event: BaseModel, username: str):
        item = self.users_client.get_user_by_username(username)
        if not item or event.customer_id and item.customer != event.customer_id:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'User not found'
            ).exc()
        return build_response(item.get_dto())

    @validate_kwargs
    def patch(self, event: UserPatchModel, username: str):
        item = self.users_client.get_user_by_username(username)
        if not item or event.customer_id and item.customer != event.customer_id:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'User not found'
            ).exc()
        params = dict()
        if event.role_name:
            params['role'] = event.role_name
            item.role = event.role_name
        to_update = UserWrapper(
            username=username,
            **params
        )
        self.users_client.update_user_attributes(to_update)
        if event.password:
            _LOG.info('Password was provided. Updating user password')
            self.users_client.set_user_password(username, event.password)

        return build_response(item.get_dto())

    @validate_kwargs
    def delete(self, event: BaseModel, username: str):
        user = self.users_client.get_user_by_username(username)
        if not user or event.customer_id and user.customer != event.customer_id:
            return build_response(code=HTTPStatus.NO_CONTENT)
        # users exists and it belongs to this customer
        self.users_client.delete_user(username)
        return build_response(code=HTTPStatus.NO_CONTENT)

    @validate_kwargs
    def whoami(self, event: BaseModel, _pe: ProcessedEvent):
        username = cast(str, _pe['cognito_username'])
        _LOG.debug(f'Getting user by username {username}')
        item = self.users_client.get_user_by_username(username)
        if not item:
            _LOG.error(f'User {username} does not exist in DB even '
                       f'though user managed to make make request')
            raise ResponseFactory(HTTPStatus.SERVICE_UNAVAILABLE).default()
        return build_response(item.get_dto())

    @validate_kwargs
    def signup(self, event: SignUpPost):
        if self._cs.get(event.customer_name):
            raise ResponseFactory(HTTPStatus.CONFLICT).message(
                f'Customer {event.customer_name} already exists'
            ).exc()
        if self.users_client.does_user_exist(event.username):
            raise ResponseFactory(HTTPStatus.CONFLICT).message(
                f'User {event.username} already exists'
            ).exc()
        customer = self._cs.build(
            name=event.customer_name,
            display_name=event.customer_display_name,
            admins=list(event.customer_admins),
            is_active=True
        )
        policy = self.rbac_service.build_policy(
            customer=event.customer_name,
            name='admin_policy',
            permissions=list(map(operator.attrgetter('value'),
                                 Permission.iter_all()))
        )
        role = self.rbac_service.build_role(
            customer=event.customer_name,
            name='admin_role',  # default main role
            policies=['admin_policy']
        )
        self.rbac_service.save(role)
        self.rbac_service.save(policy)
        self._cs.save(customer)
        self.users_client.signup_user(
            username=event.username,
            password=event.password,
            customer=event.customer_name,
            role='admin_role',
            is_system=False
        )
        _LOG.debug(f'Saving user: {event.username}')
        return build_response(content=f'The user {event.username} was created')

    @validate_kwargs
    def signin(self, event: SignInPost):
        _LOG.debug('Going to initiate the authentication flow')
        auth_result = self.users_client.authenticate_user(
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
        res = self.users_client.refresh_token(event.refresh_token)
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
        self.users_client.set_user_password(username, event.new_password)
        return build_response(code=HTTPStatus.NO_CONTENT)
