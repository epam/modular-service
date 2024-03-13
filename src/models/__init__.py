from modular_sdk.connections.mongodb_connection import MongoDBConnection
from modular_sdk.models.pynamodb_extension.base_model import \
    ABCMongoDBHandlerMixin, \
    RawBaseModel, RawBaseGSI
from modular_sdk.models.pynamodb_extension.base_safe_update_model import \
    BaseSafeUpdateModel as ModularSafeUpdateModel
from modular_sdk.models.pynamodb_extension.pynamodb_to_pymongo_adapter import \
    PynamoDBToPyMongoAdapter

from services import SP


class ModularServiceMongoDBHandlerMixin(ABCMongoDBHandlerMixin):
    @classmethod
    def mongodb_handler(cls):
        if not cls._mongodb:
            env = SP.environment_service
            cls._mongodb = PynamoDBToPyMongoAdapter(
                mongodb_connection=MongoDBConnection(
                    mongo_uri=env.mongo_uri(),
                    default_db_name=env.mongo_database()
                )
            )
        return cls._mongodb


class BaseModel(ModularServiceMongoDBHandlerMixin, RawBaseModel):
    pass


class BaseGSI(ModularServiceMongoDBHandlerMixin, RawBaseGSI):
    pass


class BaseSafeUpdateModel(ModularServiceMongoDBHandlerMixin,
                          ModularSafeUpdateModel):
    pass
