from http import HTTPStatus
import operator

from routes.route import Route

from commons.constants import (
    Endpoint,
    HTTPMethod,
    Permission,
)
from commons import NextToken
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.user_service import CognitoUserService
from services.rbac_service import RBACService
from validators.request import PolicyPost, PolicyPatch, BaseModel, BasePaginationModel
from validators.utils import validate_kwargs
from validators.response import PoliciesResponse, MessageModel, PolicyResponse

_LOG = get_logger(__name__)


class PolicyProcessor(AbstractCommandProcessor):
    def __init__(self, user_service: CognitoUserService,
                 rbac_service: RBACService):
        self.user_service = user_service
        self.rbac_service = rbac_service

    @classmethod
    def build(cls) -> 'PolicyProcessor':
        return cls(
            user_service=SERVICE_PROVIDER.user_service,
            rbac_service=SERVICE_PROVIDER.rbac_service
        )

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.POLICIES_NAME,
                HTTPMethod.GET,
                'get',
                response=(HTTPStatus.OK, PolicyResponse, None),
                permission=Permission.POLICY_DESCRIBE
            ),
            cls.route(
                Endpoint.POLICIES,
                HTTPMethod.GET,
                'query',
                response=(HTTPStatus.OK, PoliciesResponse, None),
                permission=Permission.POLICY_DESCRIBE
            ),
            cls.route(
                Endpoint.POLICIES,
                HTTPMethod.POST,
                'post',
                response=[(HTTPStatus.CREATED, PolicyResponse, None),
                          (HTTPStatus.CONFLICT, MessageModel, None)],
                permission=Permission.POLICY_CREATE
            ),
            cls.route(
                Endpoint.POLICIES_NAME,
                HTTPMethod.PATCH,
                'patch',
                response=(HTTPStatus.OK, PolicyResponse, None),
                permission=Permission.POLICY_UPDATE
            ),
            cls.route(
                Endpoint.POLICIES_NAME,
                HTTPMethod.DELETE,
                'delete',
                response=(HTTPStatus.NO_CONTENT, None, None),
                permission=Permission.POLICY_DELETE
            ),
        )

    @validate_kwargs
    def get(self, event: BaseModel, name: str):
        item = self.rbac_service.get_policy(event.customer_id, name)
        if not item:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'Policy not found'
            ).exc()
        return build_response(self.rbac_service.get_dto(item))

    @validate_kwargs
    def query(self, event: BasePaginationModel):
        cursor = self.rbac_service.iter_policies(
            customer=event.customer_id,
            limit=event.limit,
            last_evaluated_key=NextToken.from_input(event.next_token).value
        )
        items = list(cursor)
        return ResponseFactory().items(
            it=map(self.rbac_service.get_dto, items),
            next_token=NextToken(cursor.last_evaluated_key)
        ).build()

    @validate_kwargs
    def post(self, event: PolicyPost):

        if self.rbac_service.get_policy(event.customer_id, event.name):
            raise ResponseFactory(HTTPStatus.CONFLICT).message(
                f'Policy with name \'{event.name}\' already exists.'
            ).exc()

        policy = self.rbac_service.build_policy(
            customer=event.customer_id,
            name=event.name,
            permissions=sorted(map(operator.attrgetter('value'),
                                   event.permissions))
        )
        _LOG.debug('Saving policy')
        self.rbac_service.save(policy)

        return build_response(
            code=HTTPStatus.CREATED,
            content=self.rbac_service.get_dto(policy)
        )

    @validate_kwargs
    def patch(self, event: PolicyPatch, name: str):
        item = self.rbac_service.get_policy(event.customer_id, name)
        if not item:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'Policy not found'
            ).exc()
        permissions = set(item.permissions or ())
        permissions.difference_update(
            map(operator.attrgetter('value'), event.permissions_to_detach)
        )
        permissions.update(
            map(operator.attrgetter('value'), event.permissions_to_attach)
        )
        item.permissions = sorted(permissions)
        _LOG.debug('Saving policy')
        self.rbac_service.save(item)

        return build_response(self.rbac_service.get_dto(item))

    @validate_kwargs
    def delete(self, event: BaseModel, name: str):
        item = self.rbac_service.get_policy(event.customer_id, name)
        if not item:
            return build_response(code=HTTPStatus.NO_CONTENT)
        self.rbac_service.delete(item)
        return build_response(code=HTTPStatus.NO_CONTENT)
