from pynamodb.attributes import UnicodeAttribute, MapAttribute, \
    UTCDateTimeAttribute

from modular_sdk.models.base_meta import BaseMeta
from modular_sdk.models.pynamodb_extension.base_safe_update_model import \
    BaseSafeUpdateModel


class Job(BaseSafeUpdateModel):
    class Meta(BaseMeta):
        table_name = 'ModularJobs'

    job = UnicodeAttribute(hash_key=True)
    job_id = UnicodeAttribute(range_key=True)
    application = UnicodeAttribute()
    started_at = UTCDateTimeAttribute()
    stopped_at = UTCDateTimeAttribute(null=True)
    state = UnicodeAttribute()
    error_type = UnicodeAttribute(null=True)
    error_reason = UnicodeAttribute(null=True)
    meta = MapAttribute(null=True)
