from datetime import datetime
from http import HTTPStatus

from routes.route import Route

from commons import validate_params
from commons.constants import (
    EXPIRATION_ATTR,
    Endpoint,
    HTTPMethod,
    NAME_ATTR,
    POLICIES_ATTR,
    POLICIES_TO_ATTACH,
    POLICIES_TO_DETACH,
)
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.rbac.access_control_service import AccessControlService
from services.rbac.iam_service import IamService
from services.user_service import CognitoUserService

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
    def routes(cls) -> list[Route]:
        name = cls.controller_name()
        endpoint = Endpoint.ROLES.value
        return [
            Route(None, endpoint, controller=name, action='get',
                  conditions={'method': [HTTPMethod.GET]}),
            Route(None, endpoint, controller=name, action='post',
                  conditions={'method': [HTTPMethod.POST]}),
            Route(None, endpoint, controller=name, action='patch',
                  conditions={'method': [HTTPMethod.PATCH]}),
            Route(None, endpoint, controller=name, action='delete',
                  conditions={'method': [HTTPMethod.DELETE]}),
        ]

    def get(self, event):
        _LOG.debug(f'Get role event: {event}')
        role_name = event.get(NAME_ATTR)
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

    def post(self, event):
        _LOG.debug(f'Create role event: {event}')
        validate_params(event, (NAME_ATTR, EXPIRATION_ATTR, POLICIES_ATTR))

        expiration = event.get(EXPIRATION_ATTR)
        error = self._validate_expiration(value=expiration)
        if error:
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(error).exc()

        role_name = event.get(NAME_ATTR)
        policies = event.get(POLICIES_ATTR)

        if not isinstance(policies, list) and \
                not all([isinstance(i, str) for i in policies]):
            _LOG.warning(f'\'{POLICIES_ATTR}\' attribute must be a list of '
                         f'strings.')
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'\'{POLICIES_ATTR}\' attribute must be a list of strings.'
            ).exc()

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
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(error_message).exc()

        role_data = {
            NAME_ATTR: role_name,
            EXPIRATION_ATTR: expiration,
            POLICIES_ATTR: policies
        }
        _LOG.debug(f'Creating role from data: {role_data}')
        role = self.access_control_service.create_role(role_data=role_data)
        _LOG.debug('Role has been created. Saving.')
        self.access_control_service.save(role)

        _LOG.debug('Extracting role dto')
        role_dto = self.iam_service.get_role_dto(role=role)
        _LOG.debug(f'Response: {role_dto}')
        return build_response(content=role_dto)

    def patch(self, event):
        _LOG.debug(f'Patch role event" {event}')
        validate_params(event, (NAME_ATTR,))

        role_name = event.get(NAME_ATTR)

        _LOG.debug(f'Extracting role with name \'{role_name}\'')
        role = self.access_control_service.get_role(name=role_name)
        if not role:
            _LOG.warning(f'Role with name \'{role_name}\' does not exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Role with name \'{role_name}\' does not exist.'
            ).exc()

        expiration = event.get(EXPIRATION_ATTR)
        if expiration:
            error = self._validate_expiration(expiration)
            if error:
                raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(error).exc()
            _LOG.debug(f'Setting role expiration to \'{expiration}\'')
            role.expiration = expiration

        to_attach = event.get(POLICIES_TO_ATTACH)
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
        to_detach = event.get(POLICIES_TO_DETACH)
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

    def delete(self, event):
        _LOG.debug(f'Delete role event: {event}')
        validate_params(event, (NAME_ATTR,))

        role_name = event.get(NAME_ATTR)
        role = self.access_control_service.get_role(name=role_name)
        if not role:
            _LOG.debug(f'Role with name \'{role_name}\' does not exist.')
            return build_response(
                content=f'Role with name \'{role_name}\' does not exist.'
            )

        _LOG.debug('Deleting role')
        self.access_control_service.delete_entity(role)
        _LOG.debug(f'Role with name \'{role_name}\' has been deleted.')
        return build_response(content=f'Role with name \'{role_name}\' has been deleted.')

    @staticmethod
    def _validate_expiration(value):
        try:
            expiration = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            _LOG.debug(
                f'Provided \'{EXPIRATION_ATTR}\' does not match the iso '
                f'format.')
            return f'Provided \'{EXPIRATION_ATTR}\' does not match the ' \
                   f'ISO format.'

        now = datetime.now()
        if now > expiration:
            _LOG.debug('Provided expiration date has already passed.')
            return 'Provided expiration date has already passed.'
