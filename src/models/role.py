from modular_sdk.models.base_meta import BaseMeta
from commons.time_helper import utc_datetime
from pynamodb.attributes import UnicodeAttribute, ListAttribute

from models import BaseSafeUpdateModel


class Role(BaseSafeUpdateModel):
    class Meta(BaseMeta):
        table_name = 'ModularServiceRoles'

    customer = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(range_key=True)
    expiration = UnicodeAttribute(null=True)  # ISO8601, valid to date
    policies = ListAttribute(default=list)

    @property
    def has_expired(self) -> bool:
        if not self.expiration:
            return False
        return utc_datetime() >= utc_datetime(self.expiration)
