from models.policy import Policy
from models.role import Role


class IamService:
    @staticmethod
    def role_get(role_name):
        return Role.get_nullable(hash_key=role_name)

    @staticmethod
    def policy_get(policy_name: str):
        return Policy.get_nullable(hash_key=policy_name)

    @staticmethod
    def policy_batch_get(keys: list):
        policies = []
        for policy in Policy.batch_get(items=keys):
            policies.append(policy)
        return policies

    def role_batch_get(self, keys: list):
        # keys[(hash, range), (hash, range), ...]
        roles = []
        for role in Role.batch_get(items=keys):
            roles.append(role)
        return roles

    @staticmethod
    def list_policies():
        return list(Policy.scan())

    @staticmethod
    def list_roles():
        return list(Role.scan())

    @staticmethod
    def get_policy_dto(policy: Policy):
        return policy.get_json()

    @staticmethod
    def get_role_dto(role: Role):
        return role.get_json()
