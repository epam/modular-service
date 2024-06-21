import operator
from http import HTTPStatus

from routes.route import Route

from commons.constants import Endpoint, HTTPMethod, Permission
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.customer_mutator_service import CustomerMutatorService
from services.rbac_service import RBACService
from services.user_service import CognitoUserService
from validators.request import SignUpPost
from validators.response import MessageModel
from validators.utils import validate_kwargs

_LOG = get_logger(__name__)


class SignUpProcessor(AbstractCommandProcessor):
    def __init__(self, user_service: CognitoUserService,
                 rbac_service: RBACService,
                 customer_service: CustomerMutatorService):
        self.user_service = user_service
        self.rbac_service = rbac_service
        self._cs = customer_service

    @classmethod
    def build(cls) -> 'SignUpProcessor':
        return cls(
            user_service=SERVICE_PROVIDER.user_service,
            rbac_service=SERVICE_PROVIDER.rbac_service,
            customer_service=SERVICE_PROVIDER.customer_service
        )

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.SIGNUP,

                HTTPMethod.POST,
                'post',
                summary='Create a new customer, new user for that customer '
                        'admin policy and role for this user',
                response=[(HTTPStatus.CREATED, MessageModel, None),
                          (HTTPStatus.CONFLICT, MessageModel, None)],
                require_auth=False,
                permission=None
            ),
        )

    @validate_kwargs
    def post(self, event: SignUpPost):
        if self._cs.get(event.customer_name):
            raise ResponseFactory(HTTPStatus.CONFLICT).message(
                f'Customer {event.customer_name} already exists'
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
        self.user_service.save(
            username=event.username,
            password=event.password,
            role='admin_role',
            customer=event.customer_name
        )
        _LOG.debug(f'Saving user: {event.username}')
        return build_response(content=f'The user {event.username} was created')
