from models.policy import Policy
from typing import Iterable, Iterator
from models.role import Role


class IamService:
    @staticmethod
    def role_get(role_name: str) -> Role | None:
        return Role.get_nullable(hash_key=role_name)

    @staticmethod
    def policy_get(policy_name: str) -> Policy | None:
        return Policy.get_nullable(hash_key=policy_name)

    @staticmethod
    def iter_policies(names: Iterable[str]) -> Iterator[Policy]:
        for name in names:
            item = IamService.policy_get(name)
            if not item:
                continue
            yield item

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
