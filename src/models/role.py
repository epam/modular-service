from pynamodb.attributes import UnicodeAttribute, ListAttribute


from modular_sdk.models.base_meta import BaseMeta
from modular_sdk.models.pynamodb_extension.base_safe_update_model import \
    BaseSafeUpdateModel


class Role(BaseSafeUpdateModel):
    class Meta(BaseMeta):
        table_name = 'ModularRoles'

    name = UnicodeAttribute(hash_key=True)
    expiration = UnicodeAttribute(null=True)  # ISO8601, valid to date
    policies = ListAttribute(null=True, default=list)
    resource = ListAttribute(null=True, default=list)
