from pymongo import MongoClient


def replace_keys_in_dict(dictionary: dict, old_character: str,
                         new_character: str):
    new = {}
    for key, value in dictionary.items():
        if isinstance(value, dict):
            value = replace_keys_in_dict(value, old_character, new_character)
        new[key.replace(old_character, new_character)] = value
    return new


class MongoDBConnection:

    def __init__(self, mongo_uri, mongodb_db_name) -> None:
        self.mongodb_client = MongoClient(mongo_uri)
        self.mongodb_db_name = mongodb_db_name
        self.db_cache = {}

    def database(self, db_name=None):
        if not db_name:
            db_name = self.mongodb_db_name
        if not self.db_cache.get(db_name):
            self.db_cache[db_name] = self.mongodb_client.get_database(
                name=db_name)
        return self.db_cache[db_name]

    def collection(self, collection_name, db_name=None):
        database = self.database(db_name=db_name)
        return database.get_collection(collection_name)

    @classmethod
    def encode_keys(cls, dictionary: dict):
        return replace_keys_in_dict(dictionary, '.', '|#|')

    @classmethod
    def decode_keys(cls, dictionary: dict):
        return replace_keys_in_dict(dictionary, '|#|', '.')
