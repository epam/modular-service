from pynamodb.attributes import UnicodeAttribute, ListAttribute

from modular_sdk.models.base_meta import BaseMeta
from modular_sdk.models.pynamodb_extension.base_safe_update_model import \
    BaseSafeUpdateModel


class User(BaseSafeUpdateModel):
    class Meta(BaseMeta):
        table_name = 'ModularUsers'

    user_id = UnicodeAttribute(hash_key=True)
    tenants = ListAttribute(null=True, default=False)
    customer = UnicodeAttribute(null=True)
    role = UnicodeAttribute(null=True)
    password = UnicodeAttribute(null=True)
    latest_login = UnicodeAttribute(null=True)
