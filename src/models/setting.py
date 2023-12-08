from pynamodb.attributes import UnicodeAttribute
from pynamodb.exceptions import DoesNotExist

from modular_sdk.models.base_meta import BaseMeta
from modular_sdk.models.pynamodb_extension.base_model import DynamicAttribute
from modular_sdk.models.pynamodb_extension.base_safe_update_model import \
    BaseSafeUpdateModel


class Setting(BaseSafeUpdateModel):
    class Meta(BaseMeta):
        table_name = 'ModularServiceSettings'

    name = UnicodeAttribute(hash_key=True, attr_name='name')
    value = DynamicAttribute(attr_name='value')

    @classmethod
    def get_nullable(cls, hash_key, range_key=None):
        try:
            return cls.get(hash_key, range_key)
        except DoesNotExist:
            return None

    @classmethod
    def get_value(cls, hash_key, range_key=None):
        setting_item = super().get_nullable(hash_key, range_key)
        if not setting_item:
            return
        model = setting_item.dynamodb_model()
        return model
