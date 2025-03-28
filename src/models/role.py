from commons.time_helper import utc_datetime
from commons.constants import Env
from pynamodb.attributes import UnicodeAttribute, ListAttribute

from models import BaseSafeUpdateModel


class Role(BaseSafeUpdateModel):
    class Meta:
        table_name = 'ModularServiceRoles'
        region = Env.AWS_REGION.get()

    customer = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(range_key=True)
    expiration = UnicodeAttribute(null=True)  # ISO8601, valid to date
    policies = ListAttribute(default=list, of=UnicodeAttribute)

    @property
    def has_expired(self) -> bool:
        if not self.expiration:
            return False
        return utc_datetime() >= utc_datetime(self.expiration)
