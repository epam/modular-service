from modular_sdk.models.base_meta import BaseMeta
from pynamodb.attributes import BooleanAttribute, UnicodeAttribute

from models import BaseSafeUpdateModel


class User(BaseSafeUpdateModel):
    class Meta(BaseMeta):
        table_name = 'ModularUsers'

    user_id = UnicodeAttribute(hash_key=True)
    customer = UnicodeAttribute(null=True)
    is_system = BooleanAttribute(default=False)
    role = UnicodeAttribute(null=True)
    password = UnicodeAttribute()
    latest_login = UnicodeAttribute(null=True)
