from pynamodb.attributes import UnicodeAttribute, ListAttribute

from modular_sdk.models.base_meta import BaseMeta
from modular_sdk.models.pynamodb_extension.base_safe_update_model import \
    BaseSafeUpdateModel


class Policy(BaseSafeUpdateModel):
    class Meta(BaseMeta):
        table_name = 'ModularServicePolicies'

    name = UnicodeAttribute(hash_key=True)
    permissions = ListAttribute(default=list)
