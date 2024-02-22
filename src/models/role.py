from modular_sdk.models.base_meta import BaseMeta
from pynamodb.attributes import UnicodeAttribute, ListAttribute

from models import BaseSafeUpdateModel


class Role(BaseSafeUpdateModel):
    class Meta(BaseMeta):
        table_name = 'ModularServiceRoles'

    name = UnicodeAttribute(hash_key=True)
    expiration = UnicodeAttribute(null=True)  # ISO8601, valid to date
    policies = ListAttribute(default=list)
    resource = ListAttribute(default=list)
