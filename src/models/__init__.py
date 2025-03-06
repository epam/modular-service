import pymongo
from modular_sdk.models.pynamongo.adapter import PynamoDBToPymongoAdapter
from modular_sdk.models.pynamongo.models import Model, SafeUpdateModel

from commons.constants import Env


class MongoClientSingleton:
    _instance = None

    @classmethod
    def get_instance(cls) -> pymongo.MongoClient:
        if cls._instance is None:
            cls._instance = pymongo.MongoClient(Env.MONGO_URI.get())
        return cls._instance


class PynamoDBToPymongoAdapterSingleton:
    _instance = None

    @classmethod
    def get_instance(cls) -> PynamoDBToPymongoAdapter:
        if cls._instance is None:
            cls._instance = PynamoDBToPymongoAdapter(
                db=MongoClientSingleton.get_instance().get_database(
                    Env.MONGO_DATABASE.get()
                )
            )
        return cls._instance


class BaseModel(Model):
    @classmethod
    def is_mongo_model(cls) -> bool:
        return Env.is_docker()

    @classmethod
    def mongo_adapter(cls) -> PynamoDBToPymongoAdapter:
        return PynamoDBToPymongoAdapterSingleton.get_instance()


class BaseSafeUpdateModel(SafeUpdateModel):
    @classmethod
    def is_mongo_model(cls) -> bool:
        return Env.is_docker()

    @classmethod
    def mongo_adapter(cls) -> PynamoDBToPymongoAdapter:
        return PynamoDBToPymongoAdapterSingleton.get_instance()
