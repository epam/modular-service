from http import HTTPStatus

from routes.route import Route

from commons.constants import (
    EXPIRATION_ATTR,
    Endpoint,
    HTTPMethod,
    NAME_ATTR,
    POLICIES_ATTR,
    Permission
)
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from commons.time_helper import utc_iso
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.rbac.access_control_service import AccessControlService
from services.rbac.iam_service import IamService
from services.user_service import CognitoUserService
from validators.request import RoleDelete, RoleGet, RolePatch, RolePost
from validators.utils import validate_kwargs
from validators.response import RolesResponse, MessageModel

_LOG = get_logger(__name__)


class RoleProcessor(AbstractCommandProcessor):
    def __init__(self, user_service: CognitoUserService,
                 access_control_service: AccessControlService,
                 iam_service: IamService):
        self.user_service = user_service
        self.access_control_service = access_control_service
        self.iam_service = iam_service

    @classmethod
    def build(cls) -> 'RoleProcessor':
        return cls(
            user_service=SERVICE_PROVIDER.user_service,
            access_control_service=SERVICE_PROVIDER.access_control_service,
            iam_service=SERVICE_PROVIDER.iam_service,
        )

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        resp = (HTTPStatus.OK, RolesResponse, None)
        return (
            cls.route(
                Endpoint.ROLES,
                HTTPMethod.GET,
                'get',
                response=resp,
                permission=Permission.ROLE_DESCRIBE
            ),
            cls.route(
                Endpoint.ROLES,
                HTTPMethod.POST,
                'post',
                response=resp,
                permission=Permission.ROLE_CREATE
            ),
            cls.route(
                Endpoint.ROLES,
                HTTPMethod.PATCH,
                'patch',
                response=resp,
                permission=Permission.ROLE_UPDATE
            ),
            cls.route(
                Endpoint.ROLES,
                HTTPMethod.DELETE,
                'delete',
                response=(HTTPStatus.OK, MessageModel, None),
                permission=Permission.ROLE_DELETE
            ),
        )

    @validate_kwargs
    def get(self, event: RoleGet):
        role_name = event.name
        if role_name:
            _LOG.debug(f'Extracting role with name \'{role_name}\'')
            roles = [self.iam_service.role_get(role_name=role_name)]
        else:
            _LOG.debug('Extracting all available roles')
            roles = self.iam_service.list_roles()

        if not roles:
            _LOG.debug('No roles found matching given query.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'No roles found matching given query.'
            ).exc()

        roles_dto = [self.iam_service.get_role_dto(role=role) for role
                     in roles]
        _LOG.debug(f'Roles to return: {roles_dto}')
        return build_response(content=roles_dto)

    @validate_kwargs
    def post(self, event: RolePost):

        role_name = event.name
        policies = event.policies

        if self.access_control_service.role_exists(name=role_name):
            _LOG.warning(f'Role with name \'{role_name}\' already exists.')
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'Role with name \'{role_name}\' already exists.'
            ).exc()

        non_existing_policies = self.access_control_service. \
            get_non_existing_policies(policies=policies)
        if non_existing_policies:
            error_message = f'Some of the policies provided in the event ' \
                            f'don\'t exist: {", ".join(non_existing_policies)}'
            _LOG.warning(error_message)
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                error_message).exc()

        role_data = {
            NAME_ATTR: role_name,
            EXPIRATION_ATTR: utc_iso(event.expiration),
            POLICIES_ATTR: list(policies)
        }
        _LOG.debug(f'Creating role from data: {role_data}')
        role = self.access_control_service.create_role(role_data=role_data)
        _LOG.debug('Role has been created. Saving.')
        self.access_control_service.save(role)

        _LOG.debug('Extracting role dto')
        role_dto = self.iam_service.get_role_dto(role=role)
        _LOG.debug(f'Response: {role_dto}')
        return build_response(content=role_dto)

    @validate_kwargs
    def patch(self, event: RolePatch):
        _LOG.debug(f'Patch role event" {event}')

        role_name = event.name

        _LOG.debug(f'Extracting role with name \'{role_name}\'')
        role = self.access_control_service.get_role(name=role_name)
        if not role:
            _LOG.warning(f'Role with name \'{role_name}\' does not exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Role with name \'{role_name}\' does not exist.'
            ).exc()

        expiration = event.expiration
        if expiration:
            role.expiration = utc_iso(expiration)

        to_attach = event.policies_to_attach
        if to_attach:
            _LOG.debug(f'Attaching policies \'{to_attach}\'')
            non_existing = self.access_control_service. \
                get_non_existing_policies(policies=to_attach)
            if non_existing:
                _LOG.warning(f'Some of the policies provided in the request '
                             f'do not exist: \'{non_existing}\'')
                raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                    f'Some of the policies provided in the request do not exist: \'{", ".join(non_existing)}\''
                ).exc()
            role_policies = list(role.policies)
            role_policies.extend(to_attach)
            role_policies = list(set(role_policies))
            _LOG.debug(f'Role policies: {role_policies}')
            role.policies = role_policies
        to_detach = event.policies_to_detach
        if to_detach:
            _LOG.debug(f'Detaching policies \'{to_detach}\'')
            role_policies = list(role.policies)
            for policy in to_detach:
                if policy in role_policies:
                    role_policies.remove(policy)
                else:
                    _LOG.error(f'Policy \'{to_detach}\' does not exist in '
                               f'role \'{role_name}\'.')
            _LOG.debug(f'Setting role policies: {role_policies}')
            role.policies = role_policies

        _LOG.debug('Saving role')
        self.access_control_service.save(role)

        _LOG.debug('Extracting role dto')
        role_dto = self.iam_service.get_role_dto(role=role)

        _LOG.debug(f'Response: {role_dto}')
        return build_response(content=role_dto)

    @validate_kwargs
    def delete(self, event: RoleDelete):
        _LOG.debug(f'Delete role event: {event}')

        role_name = event.name
        role = self.access_control_service.get_role(name=role_name)
        if not role:
            _LOG.debug(f'Role with name \'{role_name}\' does not exist.')
            return build_response(
                content=f'Role with name \'{role_name}\' does not exist.'
            )

        _LOG.debug('Deleting role')
        self.access_control_service.delete_entity(role)
        _LOG.debug(f'Role with name \'{role_name}\' has been deleted.')
        return build_response(
            content=f'Role with name \'{role_name}\' has been deleted.')
