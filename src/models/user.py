from modular_sdk.models.base_meta import BaseMeta
from pynamodb.attributes import BooleanAttribute, UnicodeAttribute

from models import BaseSafeUpdateModel


class User(BaseSafeUpdateModel):
    class Meta(BaseMeta):
        table_name = 'ModularUsers'

    user_id = UnicodeAttribute(hash_key=True)
    password = UnicodeAttribute()
    customer = UnicodeAttribute(null=True)  # null if system user
    role = UnicodeAttribute(null=True)  # null if system user
    is_system = BooleanAttribute(default=False)
    latest_login = UnicodeAttribute(null=True)
