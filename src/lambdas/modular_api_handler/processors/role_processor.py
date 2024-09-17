from http import HTTPStatus

from routes.route import Route

from commons import NextToken
from commons.constants import Endpoint, HTTPMethod, Permission
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from commons.time_helper import utc_iso
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.rbac_service import RBACService
from validators.request import BaseModel, BasePaginationModel, RolePatch, RolePost
from validators.response import MessageModel, RoleResponse, RolesResponse
from validators.utils import validate_kwargs

_LOG = get_logger(__name__)


class RoleProcessor(AbstractCommandProcessor):
    def __init__(self, rbac_service: RBACService):
        self.rbac_service = rbac_service

    @classmethod
    def build(cls) -> 'RoleProcessor':
        return cls(
            rbac_service=SERVICE_PROVIDER.rbac_service
        )

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.ROLES_NAME,
                HTTPMethod.GET,
                'get',
                response=(HTTPStatus.OK, RoleResponse, None),
                permission=Permission.ROLE_DESCRIBE
            ),
            cls.route(
                Endpoint.ROLES,
                HTTPMethod.GET,
                'query',
                response=(HTTPStatus.OK, RolesResponse, None),
                permission=Permission.ROLE_DESCRIBE
            ),
            cls.route(
                Endpoint.ROLES,
                HTTPMethod.POST,
                'post',
                response=[(HTTPStatus.CREATED, RoleResponse, None),
                          (HTTPStatus.CONFLICT, MessageModel, None)],
                permission=Permission.ROLE_CREATE
            ),
            cls.route(
                Endpoint.ROLES_NAME,
                HTTPMethod.PATCH,
                'patch',
                response=(HTTPStatus.OK, RoleResponse, None),
                permission=Permission.ROLE_UPDATE
            ),
            cls.route(
                Endpoint.ROLES_NAME,
                HTTPMethod.DELETE,
                'delete',
                response=(HTTPStatus.NO_CONTENT, None, None),
                permission=Permission.ROLE_DELETE
            ),
        )

    @validate_kwargs
    def get(self, event: BaseModel, name: str):
        item = self.rbac_service.get_role(event.customer_id, name)
        if not item:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'Role not found'
            ).exc()
        return build_response(self.rbac_service.get_dto(item))

    @validate_kwargs
    def query(self, event: BasePaginationModel):
        cursor = self.rbac_service.iter_roles(
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
    def post(self, event: RolePost):
        if self.rbac_service.get_role(event.customer_id, event.name):
            raise ResponseFactory(HTTPStatus.CONFLICT).message(
                f'Role with name \'{event.name}\' already exists.'
            ).exc()
        for policy in event.policies:
            if not self.rbac_service.get_policy(event.customer_id, policy):
                raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                    f'Policy {policy} does not exist'
                ).exc()
        role = self.rbac_service.build_role(
            customer=event.customer_id,
            name=event.name,
            policies=list(event.policies)
        )
        _LOG.debug('Saving role')
        self.rbac_service.save(role)

        return build_response(
            code=HTTPStatus.CREATED,
            content=self.rbac_service.get_dto(role)
        )

    @validate_kwargs
    def patch(self, event: RolePatch, name: str):
        item = self.rbac_service.get_role(event.customer_id, name)
        if not item:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'Role not found'
            ).exc()
        policies = set(item.policies or ())
        policies.difference_update(event.policies_to_detach)
        policies.update(event.policies_to_attach)
        item.policies = list(policies)
        if event.expiration:
            item.expiration = utc_iso(event.expiration)
        _LOG.debug('Saving role')
        self.rbac_service.save(item)
        return build_response(self.rbac_service.get_dto(item))

    @validate_kwargs
    def delete(self, event: BaseModel, name: str):
        item = self.rbac_service.get_role(event.customer_id, name)
        if not item:
            return build_response(code=HTTPStatus.NO_CONTENT)
        self.rbac_service.delete(item)
        return build_response(code=HTTPStatus.NO_CONTENT)
