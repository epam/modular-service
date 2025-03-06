from pynamodb.attributes import BooleanAttribute, UnicodeAttribute
from commons.constants import Env
from modular_sdk.models.pynamongo.attributes import BinaryAttribute

from models import BaseSafeUpdateModel


class User(BaseSafeUpdateModel):
    class Meta:
        table_name = 'ModularUsers'
        region = Env.AWS_REGION.get()

    user_id = UnicodeAttribute(hash_key=True)
    password = BinaryAttribute()
    customer = UnicodeAttribute(null=True)  # null if system user
    role = UnicodeAttribute(null=True)  # null if system user
    is_system = BooleanAttribute(default=False)
    latest_login = UnicodeAttribute(null=True)
    created_at = UnicodeAttribute(null=True)
