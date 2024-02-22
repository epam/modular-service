from datetime import datetime, timedelta

from commons.log_helper import get_logger
from models.policy import Policy
from models.role import Role
from services.rbac.endpoint_to_permission_mapping import ALL_PERMISSIONS
from services.rbac.iam_service import IamService
from services.user_service import CognitoUserService

_LOG = get_logger(__name__)

PARAM_NAME = 'name'
PARAM_PERMISSIONS = 'permissions'
PARAM_EXPIRATION = 'expiration'
PARAM_REQUEST_PATH = 'request_path'
PARAM_TARGET_USER = 'target_user'


class AccessControlService:

    def __init__(self, iam_service: IamService,
                 user_service: CognitoUserService):
        self.iam_service = iam_service
        self.user_service = user_service

    def is_allowed_to_access(self, username: str,
                             target_permission: str) -> bool:

        _LOG.debug(f'Checking user permissions '
                   f'on \'{target_permission}\' action')
        role_name = self.user_service.get_user_role_name(user=username)
        role = self.iam_service.role_get(role_name=role_name)

        if not role:
            _LOG.debug(f'Specified role with name: {role_name} does not exist')
            return False
        if AccessControlService.is_role_expired(role=role):
            _LOG.debug(f'Specified role with name: {role_name}  is expired')
            return False
        for policy in self.iam_service.iter_policies(set(role.policies)):
            if target_permission in policy.permissions:
                return True
        return False

    def get_role(self, name: str):
        return self.iam_service.role_get(role_name=name)

    def get_policy(self, name: str):
        return self.iam_service.policy_get(policy_name=name)

    def policy_exists(self, name: str) -> bool:
        # todo remove
        return bool(self.get_policy(name=name))

    def role_exists(self, name: str) -> bool:
        # todo remove
        return bool(self.get_role(name=name))

    @staticmethod
    def get_role_dto(role: Role):
        return role.get_json()

    @staticmethod
    def get_policy_dto(policy: Policy):
        return policy.get_json()

    @staticmethod
    def delete_entity(entity: Role | Policy):
        return entity.delete()

    def create_policy(self, policy_data: dict):
        name = policy_data.get(PARAM_NAME)
        if self.policy_exists(name=name):
            _LOG.warning(f'Policy  with name \'{name}\' already exists')

        return Policy(**policy_data)

    def create_role(self, role_data: dict):
        name = role_data.get(PARAM_NAME)
        if self.role_exists(name=name):
            _LOG.warning(f'Role with name \'{name}\' already exists')

        return Role(**role_data)

    @staticmethod
    def save(access_conf_object: Role | Policy):
        access_conf_object.save()

    @staticmethod
    def is_role_expired(role: Role):
        role_expiration_datetime = role.expiration
        if isinstance(role_expiration_datetime, str):
            role_expiration_datetime = datetime.fromisoformat(
                role_expiration_datetime)
        now = datetime.now()
        return now >= role_expiration_datetime

    @staticmethod
    def get_non_existing_permissions(permissions: list | set) -> set:
        return set(permissions) - ALL_PERMISSIONS

    def get_non_existing_policies(self, policies: list | set) -> list:
        nonexistent = []
        for policy in policies:
            if not self.policy_exists(name=policy):
                nonexistent.append(policy)
        return nonexistent

    @staticmethod
    def get_admin_permissions() -> list:
        return list(ALL_PERMISSIONS)

    @staticmethod
    def get_role_default_expiration():
        current = datetime.now()
        expiration = current + timedelta(3 * 30)
        return expiration.isoformat()
