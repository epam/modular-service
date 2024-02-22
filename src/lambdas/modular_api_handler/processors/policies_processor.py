from http import HTTPStatus

from routes.route import Route

from commons import validate_params
from commons.constants import (
    Endpoint,
    HTTPMethod,
    NAME_ATTR,
    PERMISSIONS_ADMIN_ATTR,
    PERMISSIONS_ATTR,
    PERMISSIONS_TO_ATTACH,
    PERMISSIONS_TO_DETACH,
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


class PolicyProcessor(AbstractCommandProcessor):
    def __init__(self, user_service: CognitoUserService,
                 access_control_service: AccessControlService,
                 iam_service: IamService):
        self.user_service = user_service
        self.access_control_service = access_control_service
        self.iam_service = iam_service

    @classmethod
    def build(cls) -> 'PolicyProcessor':
        return cls(
            user_service=SERVICE_PROVIDER.user_service,
            access_control_service=SERVICE_PROVIDER.access_control_service,
            iam_service=SERVICE_PROVIDER.iam_service,
        )

    @classmethod
    def routes(cls) -> list[Route]:
        name = cls.controller_name()
        endpoint = Endpoint.POLICIES.value
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
        _LOG.debug(f'Get policy event: {event}')
        policy_name = event.get(NAME_ATTR)
        if policy_name:
            _LOG.debug(f'Extracting policy with name \'{policy_name}\'')
            policies = [self.iam_service.policy_get(policy_name=policy_name)]
        else:
            _LOG.debug('Extracting all available policies')
            policies = self.iam_service.list_policies()

        if not policies or policies \
                and all([policy is None for policy in policies]):
            _LOG.debug('No policies found matching given query.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'No policies found matching given query.'
            ).exc()

        policies_dto = [self.iam_service.get_policy_dto(policy) for policy in
                        policies]
        _LOG.debug(f'Policies to return: {policies_dto}')
        return build_response(content=policies_dto)

    def post(self, event):
        _LOG.debug(f'Create policy event: {event}')
        validate_params(event, (NAME_ATTR,))

        if not event.get(PERMISSIONS_ATTR) \
                and not event.get(PERMISSIONS_ADMIN_ATTR):
            required = ", ".join((PERMISSIONS_ATTR, PERMISSIONS_ADMIN_ATTR))
            _LOG.debug(f'One of the attributes \'{required}\' must be '
                       f'specified')
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'One of the attributes \'{required}\' must be specified'
            ).exc()
        policy_name = event.get(NAME_ATTR)

        if self.access_control_service.policy_exists(name=policy_name):
            _LOG.debug(f'Policy with name \'{policy_name}\' already exists.')
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'Policy with name \'{policy_name}\' already exists.'
            ).exc()

        permissions = event.get(PERMISSIONS_ATTR)
        if permissions:
            non_existing = self.access_control_service. \
                get_non_existing_permissions(permissions=permissions)

            if non_existing:
                _LOG.debug(f'Some of the specified permissions don\'t exist: '
                           f'{", ".join(non_existing)}')
                raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                    f'Some of the specified permissions don\'t exist: {", ".join(non_existing)}'
                ).exc()
        elif event.get(PERMISSIONS_ADMIN_ATTR, None):
            permissions = self.access_control_service.get_admin_permissions()

        policy_data = {
            NAME_ATTR: policy_name,
            PERMISSIONS_ATTR: permissions
        }
        _LOG.debug(f'Going to create policy with data: {policy_data}')
        policy = self.access_control_service.create_policy(
            policy_data=policy_data)

        _LOG.debug('Saving policy')
        self.access_control_service.save(policy)

        policy_dto = self.iam_service.get_policy_dto(policy=policy)
        _LOG.debug(f'Response: {policy_dto}')
        return build_response(content=policy_dto)

    def patch(self, event):
        _LOG.debug(f'Update policy event: {event}')
        validate_params(event, (NAME_ATTR,))

        policy_name = event.get(NAME_ATTR)
        permissions = event.get(PERMISSIONS_ATTR)
        to_attach = event.get(PERMISSIONS_TO_ATTACH)
        to_detach = event.get(PERMISSIONS_TO_DETACH)

        if not any(i for i in (permissions, to_attach, to_detach)):
            required = ', '.join((PERMISSIONS_ATTR, PERMISSIONS_TO_ATTACH,
                                  PERMISSIONS_TO_DETACH))
            _LOG.debug(f'One of the following arguments \'{required}\' must '
                       f'be provided.')
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'One of the following arguments \'{required}\' must be provided.'
            ).exc()
        policy = self.access_control_service.get_policy(name=policy_name)
        if not policy:
            _LOG.debug(f'Policy with name \'{policy_name}\' does not exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Policy with name \'{policy_name}\' does not exist.'
            ).exc()
        if permissions:
            _LOG.debug(f'Going to reset permissions for policy with name '
                       f'\'{policy_name}\'. Permissions: {permissions}')
            non_existing = self.access_control_service. \
                get_non_existing_permissions(permissions=permissions)

            if non_existing:
                _LOG.debug(f'Some of the specified permissions don\'t exist: '
                           f'{", ".join(non_existing)}')
                raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                    f'Some of the specified permissions don\'t exist: {", ".join(non_existing)}'
                ).exc()
            policy.permissions = permissions
        else:
            if to_attach:
                _LOG.debug(f'going to attach permissions to policy: '
                           f'\'{to_attach}\'')

                policy_permissions = list(policy.permissions)
                policy_permissions.extend(to_attach)
                policy_permissions = list(set(policy_permissions))
                policy.permissions = policy_permissions
            if to_detach:
                _LOG.debug(f'going to detach permissions from policy: '
                           f'\'{to_detach}\'')
                policy_permissions = list(policy.permissions)
                for permission in to_detach:
                    if permission in policy_permissions:
                        _LOG.debug(f'Removing permission: {permission}')
                        policy_permissions.remove(permission)
                    else:
                        _LOG.debug(f'Permission \'{permission}\' does not '
                                   f'exist in policy.')
                policy.permissions = policy_permissions
        _LOG.debug('Saving policy')
        self.access_control_service.save(policy)

        policy_dto = self.iam_service.get_policy_dto(policy=policy)
        _LOG.debug(f'Response: {policy_dto}')
        return build_response(content=policy_dto)

    def delete(self, event):
        _LOG.debug(f'Delete policy event: {event}')
        validate_params(event, (NAME_ATTR,))

        policy_name = event.get(NAME_ATTR)
        _LOG.debug(f'Extracting policy with name \'{policy_name}\'')
        policy = self.access_control_service.get_policy(name=policy_name)
        if not policy:
            _LOG.debug(f'Policy with name \'{policy_name}\' does not exist.')
            return build_response(content=f'Policy with name \'{policy_name}\' does not exist.')
        _LOG.debug('Deleting policy')
        self.access_control_service.delete_entity(policy)
        _LOG.debug(f'Policy with name \'{policy_name}\' has been deleted.')
        return build_response(content=f'Policy with name \'{policy_name}\' has been deleted.')
