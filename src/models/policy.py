from pynamodb.attributes import UnicodeAttribute, ListAttribute

from modular_sdk.models.base_meta import BaseMeta
from models import BaseSafeUpdateModel


class Policy(BaseSafeUpdateModel):
    class Meta(BaseMeta):
        table_name = 'ModularServicePolicies'

    customer = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(range_key=True)
    permissions = ListAttribute(default=list)
