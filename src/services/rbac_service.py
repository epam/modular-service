from datetime import datetime
from itertools import chain
from typing import Generator

from pynamodb.pagination import ResultIterator

from commons.constants import Permission
from commons.time_helper import utc_iso
from models.policy import Policy
from models.role import Role


class RBACService:
    @staticmethod
    def build_role(customer: str, name: str, policies: list[str], 
                   expiration: datetime | None = None) -> Role:
        return Role(
            customer=customer,
            name=name,
            policies=policies,
            expiration=utc_iso(expiration) if expiration else None
        )

    @staticmethod
    def build_policy(customer: str, name: str, permissions: list[str]
                     ) -> Policy:
        return Policy(
            customer=customer,
            name=name,
            permissions=permissions,
        )

    @staticmethod
    def save(item: Role | Policy) -> None:
        item.save()

    @staticmethod
    def delete(item: Role | Policy) -> None:
        item.delete()

    @staticmethod
    def get_dto(item: Role | Policy) -> dict:
        return item.get_json()

    @staticmethod
    def get_role(customer: str, name: str) -> Role | None:
        return Role.get_nullable(hash_key=customer, range_key=name)

    @staticmethod
    def get_policy(customer: str, name: str) -> Policy | None:
        return Policy.get_nullable(hash_key=customer, range_key=name)

    @staticmethod
    def iter_roles(customer: str, limit: int | None = None, 
                   last_evaluated_key: dict | None = None, 
                   rate_limit: int | None = None) -> ResultIterator[Role]:
        return Role.query(
            hash_key=customer,
            limit=limit,
            last_evaluated_key=last_evaluated_key,
            rate_limit=rate_limit
        )

    @staticmethod
    def iter_policies(customer: str, limit: int | None = None, 
                      last_evaluated_key: dict | None = None, 
                      rate_limit: int | None = None) -> ResultIterator[Policy]:
        return Policy.query(
            hash_key=customer,
            limit=limit,
            last_evaluated_key=last_evaluated_key,
            rate_limit=rate_limit
        )

    def iter_role_policies(self, role: Role) -> Generator[Policy, None, None]:
        yielded = set()
        for name in role.policies:
            if name in yielded:
                continue
            item = self.get_policy(role.customer, name)
            if item:
                yield item
            yielded.add(name)

    def is_allowed(self, customer: str, role: str, permission: Permission
                   ) -> bool:
        """
        Tells whether the given permission is allowed by the role inside
        customer
        :param customer:
        :param role:
        :param permission: target permission
        :return:
        """

        role = self.get_role(customer, role)
        if not role or role.has_expired:
            return False
        it = chain.from_iterable(
            policy.permissions for policy in self.iter_role_policies(role)
        )
        for user_permission in it:
            if self.does_permission_match(permission.value, user_permission):
                return True
        return False

    @staticmethod
    def does_permission_match(target_permission: str, permission: str) -> bool:
        """
        Our permissions adhere to such a format "domain:action".
        :param target_permission: permission a user want to access.
        It's not supposed to contain '*'. Must be a solid perm.
        to access one endpoint
        :param permission: permission a user has
        :return:
        """
        if ':' not in target_permission:
            return False
        if ':' not in permission:
            return False

        tp_domain, tp_action = map(
            str.strip, target_permission.split(':', maxsplit=2))
        p_domain, p_action = map(
            str.strip, permission.split(':', maxsplit=2))

        _domain_match = tp_domain == p_domain or p_domain == '*'
        _action_match = tp_action == p_action or p_action == '*'
        return _domain_match and _action_match
