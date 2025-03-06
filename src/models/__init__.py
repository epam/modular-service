from modular_sdk.connections.mongodb_connection import MongoDBConnection
from modular_sdk.models.pynamodb_extension.base_model import (
    ABCMongoDBHandlerMixin,
    RawBaseGSI,
    RawBaseModel,
)
from modular_sdk.models.pynamodb_extension.base_safe_update_model import (
    BaseSafeUpdateModel as ModularSafeUpdateModel,
)
from modular_sdk.models.pynamodb_extension.pynamodb_to_pymongo_adapter import (
    PynamoDBToPyMongoAdapter,
)
from commons.constants import Env

from services import SP


ADAPTER = None
MONGO_CLIENT = None


_env = SP.environment_service
if _env.is_docker():
    ADAPTER = PynamoDBToPyMongoAdapter(
        mongodb_connection=MongoDBConnection(
            mongo_uri=_env.mongo_uri(),
            default_db_name=_env.mongo_database()
        )
    )
    MONGO_CLIENT = ADAPTER.mongodb.client


class ModularServiceMongoDBHandlerMixin(ABCMongoDBHandlerMixin):
    @classmethod
    def mongodb_handler(cls):
        if not cls._mongodb:
            cls._mongodb = ADAPTER
        return cls._mongodb

    is_docker = Env.SERVICE_MODE.get() == 'docker'


class BaseModel(ModularServiceMongoDBHandlerMixin, RawBaseModel):
    pass


class BaseGSI(ModularServiceMongoDBHandlerMixin, RawBaseGSI):
    pass


class BaseSafeUpdateModel(ModularServiceMongoDBHandlerMixin,
                          ModularSafeUpdateModel):
    pass
