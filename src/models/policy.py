from pynamodb.attributes import UnicodeAttribute, ListAttribute

from commons.constants import Env
from models import BaseSafeUpdateModel


class Policy(BaseSafeUpdateModel):
    class Meta:
        table_name = 'ModularServicePolicies'
        region = Env.AWS_REGION.get()

    customer = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(range_key=True)
    permissions = ListAttribute(default=list)
